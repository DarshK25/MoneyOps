"""
Backend HTTP adapter: http client for backend core API
Handles all communication with Springboot backend
Uses gRPC for low-latency internal calls, falls back to HTTP
"""

from typing import Dict, Any, List, Optional, Literal
import httpx
import re
import datetime
import time
import json
from urllib.parse import urlsplit, parse_qsl
from pydantic import BaseModel, Field, field_validator
from rapidfuzz import process, fuzz

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Conditionally import gRPC client
if settings.GRPC_ENABLED:
    from app.adapters.grpc_client import grpc_client
    logger.info("gRPC client enabled for backend adapter")
else:
    grpc_client = None

# Conditionally import Redis for caching
try:
    from app.integrations.redis_client import get_redis, cache_get, cache_set, cache_delete
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


def normalize_business_id(business_id: Optional[Any], default: str = "1") -> str:
    """Convert nullable or placeholder business ids into a backend-safe numeric string."""
    if business_id is None:
        return default

    value = str(business_id).strip()
    if not value or value.lower() in {"default", "none", "null", "undefined"}:
        return default

    return value if value.isdigit() else default


class OrgIsolationError(Exception):
    """Raised when an operation violates organization isolation rules."""

    pass


class ClientRecord(BaseModel):
    id: str
    display_name: str
    backend_name: str
    email: Optional[str] = None
    status: Literal["ACTIVE", "INACTIVE"]
    org_id: str


class BackendResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: int


class BackendHttpAdapter:
    def __init__(
        self, base_url: Optional[str] = None, auth_token: Optional[str] = None
    ):
        self.base_url = base_url or settings.BACKEND_BASE_URL
        self.timeout = getattr(settings, "BACKEND_TIMEOUT", 30)
        self.auth_token = auth_token

        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "MoneyOps-AI-Gateway/1.0",
            "X-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
        }

        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=self.timeout, headers=default_headers
        )

        # Use Redis for caching if available, otherwise fallback to in-memory
        self._use_redis_cache = REDIS_AVAILABLE and settings.REDIS_HOST
        if not self._use_redis_cache:
            self._onboarding_cache: Dict[str, tuple[bool, float]] = {}
            self._org_uuid_cache: Dict[str, str] = {}
            self._ONBOARDING_TTL = 300

        # gRPC availability
        self._grpc_enabled = settings.GRPC_ENABLED and grpc_client is not None

        logger.info("backend_adapter_initialized", base_url=self.base_url, redis_cache=self._use_redis_cache, grpc_enabled=self._grpc_enabled)

    @staticmethod
    def _unwrap_collection(data: Any) -> List[Dict[str, Any]]:
        """Normalize Spring Page, ApiResponse, and raw list payloads into item lists."""
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return data["data"]
            if isinstance(data.get("data"), dict):
                return BackendHttpAdapter._unwrap_collection(data["data"])
            if isinstance(data.get("content"), list):
                return data["content"]
            for key in ("clients", "invoices", "transactions", "items", "results"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    async def _try_grpc(self, grpc_func, *args, fallback_func=None, **kwargs) -> BackendResponse:
        """Try gRPC call, fall back to HTTP on failure."""
        if self._grpc_enabled:
            try:
                result = await grpc_func(*args, **kwargs)
                if result.get("success"):
                    return BackendResponse(
                        success=True,
                        data=result.get("data"),
                        status_code=200,
                    )
                # gRPC call succeeded but returned error - log and fall back
                logger.warning("grpc_call_returned_error", error=result.get("error"), fallback=True)
            except Exception as e:
                logger.warning("grpc_call_exception", error=str(e), fallback=True)
        
        # Fall back to HTTP
        if fallback_func:
            return await fallback_func()
        return BackendResponse(success=False, error="No fallback available", status_code=500)

    async def resolve_org_uuid(self, user_id: str) -> Optional[str]:
        if not user_id or user_id == "unknown":
            return None

        if self._use_redis_cache:
            cache_key = f"org_uuid:{user_id}"
            try:
                r = await get_redis()
                cached = await r.get(cache_key)
                if cached:
                    return cached
            except Exception as e:
                logger.warning("redis_cache_get_failed", key=cache_key, error=str(e))
        elif user_id in self._org_uuid_cache:
            return self._org_uuid_cache[user_id]

        resp = await self.get_onboarding_status(user_id)
        if resp.success and resp.data:
            data = (
                resp.data.get("data")
                if isinstance(resp.data, dict) and "data" in resp.data
                else resp.data
            )
            org_uuid = (
                data.get("orgId") or data.get("orgUuid") or data.get("organizationId")
            )
            if org_uuid:
                if self._use_redis_cache:
                    try:
                        r = await get_redis()
                        await r.setex(f"org_uuid:{user_id}", 300, org_uuid)
                    except Exception as e:
                        logger.warning("redis_cache_set_failed", error=str(e))
                else:
                    self._org_uuid_cache[user_id] = org_uuid
                return org_uuid
        return None

    async def _get_headers(
        self,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Build headers with resolved internal org UUID."""
        headers = self.client.headers.copy()

        if org_id:
            internal_uuid = org_id
            if org_id.startswith("org_") or org_id.startswith("user_"):
                resolution_key = user_id or org_id
                resolved = await self.resolve_org_uuid(resolution_key)
                if resolved:
                    internal_uuid = resolved
            headers["X-Org-Id"] = internal_uuid

        if user_id:
            headers["X-User-Id"] = user_id

        if extra_headers:
            headers.update(extra_headers)

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> BackendResponse:
        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        req_headers = await self._get_headers(org_id, user_id, headers)

        try:
            response = await self.client.request(
                method=method, url=url, json=data, params=params, headers=req_headers
            )
            success = 200 <= response.status_code < 300

            try:
                response_data = response.json() if response.text else None
            except:
                response_data = {"text": response.text}

            error_msg = (
                response_data.get("message") or response_data.get("error")
                if isinstance(response_data, dict)
                else None
            )
            if not success and not error_msg:
                error_msg = f"Backend error: {response.status_code}"

            return BackendResponse(
                success=success,
                data=response_data,
                status_code=response.status_code,
                error=error_msg,
            )
        except Exception as e:
            logger.error("backend_request_error", endpoint=endpoint, error=str(e))
            return BackendResponse(success=False, error=str(e), status_code=500)

    async def get_onboarding_status(self, user_id: str) -> BackendResponse:
        if self._use_redis_cache:
            cache_key = f"onboarding:{user_id}"
            try:
                r = await get_redis()
                cached_data = await r.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return BackendResponse(success=True, data=data, status_code=200)
            except Exception as e:
                logger.warning("redis_cache_get_failed", key=cache_key, error=str(e))
        elif user_id in self._onboarding_cache:
            cached_data, ts = self._onboarding_cache[user_id]
            if time.time() - ts < self._ONBOARDING_TTL:
                return BackendResponse(success=True, data=cached_data, status_code=200)

        resp = await self._request(
            "GET", "/api/onboarding/status", params={"userId": user_id}
        )
        if resp.success and resp.data:
            data = (
                resp.data.get("data")
                if isinstance(resp.data, dict) and "data" in resp.data
                else resp.data
            )
            if self._use_redis_cache:
                try:
                    r = await get_redis()
                    await r.setex(f"onboarding:{user_id}", 300, json.dumps(data))
                except Exception as e:
                    logger.warning("redis_cache_set_failed", error=str(e))
            else:
                self._onboarding_cache[user_id] = (data, time.time())
            resp.data = data
        return resp

    async def get_my_organization(self, user_id: str) -> BackendResponse:
        resp = await self._request("GET", "/api/org/my", user_id=user_id)
        if resp.success and resp.data:
            resp.data = (
                resp.data.get("data")
                if isinstance(resp.data, dict) and "data" in resp.data
                else resp.data
            )
        return resp

    async def create_invoice_direct(
        self, org_id: str, user_id: str, payload: Dict[str, Any]
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.create_invoice,
            org_id, payload,
            fallback_func=lambda: self._request(
                "POST", "/api/invoices", data=payload, org_id=org_id, user_id=user_id
            )
        )
        return grpc_result

    async def validate_team_action_code(
        self, org_id: str, user_id: str, team_action_code: str
    ) -> BackendResponse:
        return await self._request(
            "POST",
            f"/api/org/{org_id}/team-security-code/validate",
            data={"teamActionCode": team_action_code},
            org_id=org_id,
            user_id=user_id,
        )

    async def get_clients(
        self, org_id: str, limit: int = 100, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.get_clients,
            org_id, limit,
            fallback_func=lambda: self._request(
                "GET", "/api/clients", params={"page": 0, "size": limit}, org_id=org_id, user_id=user_id
            )
        )
        if grpc_result.success and grpc_result.data:
            return grpc_result.data
        
        # Fallback HTTP response
        resp = await self._request(
            "GET", "/api/clients", params={"page": 0, "size": limit}, org_id=org_id, user_id=user_id
        )
        if resp.success and resp.data:
            return self._unwrap_collection(resp.data)
        return []

    async def get_invoices(
        self,
        org_id: str,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.get_invoices,
            org_id, status,
            fallback_func=lambda: self._request(
                "GET", "/api/invoices", params={"page": 0, "size": limit, **({"status": status} if status else {})}, org_id=org_id, user_id=user_id
            )
        )
        if grpc_result.success:
            return grpc_result
        
        # Fallback HTTP
        params = {"page": 0, "size": limit}
        if status:
            params["status"] = status
        resp = await self._request(
            "GET", "/api/invoices", params=params, org_id=org_id, user_id=user_id
        )
        if resp.success:
            resp.data = self._unwrap_collection(resp.data)
        return resp

    async def get_invoice(
        self,
        invoice_id: str,
        org_id: str,
        user_id: Optional[str] = None,
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.get_invoice,
            invoice_id, org_id,
            fallback_func=lambda: self._request(
                "GET", f"/api/invoices/{invoice_id}", org_id=org_id, user_id=user_id
            )
        )
        return grpc_result

    async def get_finance_metrics(
        self, business_id: Optional[Any], org_id: str, user_id: Optional[str] = None
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.get_finance_metrics,
            org_id, normalize_business_id(business_id),
            fallback_func=lambda: self._request(
                "GET",
                "/api/finance-intelligence/metrics",
                params={"businessId": normalize_business_id(business_id)},
                org_id=org_id,
                user_id=user_id,
            )
        )
        return grpc_result

    async def get_financial_summary(
        self, org_id: str, user_id: Optional[str] = None
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.get_financial_summary,
            org_id,
            fallback_func=lambda: self._request(
                "GET", "/api/transactions/summary", org_id=org_id, user_id=user_id
            )
        )
        return grpc_result

    async def send_collection_email(
        self,
        invoice_id: str,
        client_email: str,
        client_name: str,
        invoice_number: str,
        amount: float,
        due_date: str,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tone: str = "gentle",
    ) -> dict:
        # Try gRPC first
        if self._grpc_enabled and grpc_client:
            try:
                result = await grpc_client.send_collection_email(
                    invoice_id=invoice_id,
                    client_email=client_email,
                    client_name=client_name,
                    invoice_number=invoice_number,
                    amount=amount,
                    due_date=due_date,
                    org_id=org_id,
                    tone=tone,
                )
                return {
                    "sent": result.get("success", False),
                    "recipient": client_email,
                    "status_code": 200 if result.get("success") else 500,
                    "error": result.get("error"),
                    "source": "grpc",
                }
            except Exception as e:
                logger.error("grpc_send_email_error", invoice_id=invoice_id, error=str(e))
                # Fall through to HTTP

        payload = {
            "type": "PAYMENT_REMINDER",
            "recipientEmail": client_email,
            "recipientName": client_name,
            "templateData": {
                "invoiceId": invoice_id,
                "invoiceNumber": invoice_number,
                "amount": amount,
                "dueDate": due_date,
                "businessName": settings.BUSINESS_NAME,
                "tone": tone,
            },
        }
        resp = await self._request(
            "POST",
            "/api/notifications/email",
            data=payload,
            org_id=org_id,
            user_id=user_id,
        )
        return {
            "sent": bool(resp.success),
            "recipient": client_email,
            "status_code": resp.status_code,
            "error": resp.error,
            "source": "http",
        }

    async def create_client(
        self, org_id: str, user_id: Optional[str], payload: Dict[str, Any]
    ) -> BackendResponse:
        # Try gRPC first
        grpc_result = await self._try_grpc(
            grpc_client.create_client,
            org_id, payload,
            fallback_func=lambda: self._request(
                "POST", "/api/clients", data=payload, org_id=org_id, user_id=user_id
            )
        )
        return grpc_result

    async def get(
        self,
        endpoint: str,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Generic GET helper used by the unified moneyops agent."""
        parsed = urlsplit(endpoint)
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        resp = await self._request(
            "GET",
            parsed.path or endpoint,
            params=params or None,
            headers=headers,
            org_id=org_id,
            user_id=user_id,
        )
        if not resp.success:
            raise RuntimeError(resp.error or f"GET {endpoint} failed")
        return resp.data

    async def post(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Any:
        """Generic POST helper used by the unified moneyops agent."""
        resp = await self._request(
            "POST",
            endpoint,
            data=payload,
            headers=headers,
            org_id=org_id,
            user_id=user_id,
        )
        if not resp.success:
            raise RuntimeError(resp.error or f"POST {endpoint} failed")
        return resp.data

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Any:
        """Generic DELETE helper used by the unified moneyops agent."""
        resp = await self._request(
            "DELETE",
            endpoint,
            headers=headers,
            org_id=org_id,
            user_id=user_id,
        )
        if not resp.success:
            raise RuntimeError(resp.error or f"DELETE {endpoint} failed")
        return resp.data

    def _build_client_params(self, org_id: Optional[str] = None, **kwargs) -> dict:
        if not org_id:
            raise OrgIsolationError("Organization ID (org_id) is required for client operations")
        params = dict(kwargs)
        params["org_id"] = org_id
        return params

    def set_auth_token(self, token: str):
        self.auth_token = token
        self.client.headers["Authorization"] = f"Bearer {token}"


_backend_adapter_instance: Optional[BackendHttpAdapter] = None


def get_backend_adapter(auth_token: Optional[str] = None) -> BackendHttpAdapter:
    """Return a shared backend adapter instance for the voice and agent paths."""
    global _backend_adapter_instance
    if auth_token:
        return BackendHttpAdapter(auth_token=auth_token)
    if _backend_adapter_instance is None:
        _backend_adapter_instance = BackendHttpAdapter()
    return _backend_adapter_instance
