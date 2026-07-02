"""
TReDS (Trade Receivables Discounting System) API Integration Client.

Supports RXIL, M1xchange, and Invoicemart platforms for invoice discounting.
Provides real API integration with proper error handling and retries.
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.utils.logger import get_logger
from app.schemas.treds import (
    TReDSPlatform,
    DiscountingRateResponse,
    DiscountInvoiceResponse,
    InvoiceDiscountingRequest,
    DiscountingStatus,
)

logger = get_logger(__name__)


class TReDSResponse(BaseModel):
    """Base response from TReDS API"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class TReDSClient:
    """
    TReDS API Client for invoice discounting.

    Implements RXIL API integration patterns with support for
    M1xchange and Invoicemart.
    """

    def __init__(self, platform: TReDSPlatform = TReDSPlatform.RXIL):
        self.platform = platform
        self.base_url = self._get_base_url(platform)
        self.api_key = settings.TREDS_API_KEY
        self.enabled = settings.TREDS_ENABLED
        self._client: Optional[httpx.AsyncClient] = None
        self._auth_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _get_base_url(self, platform: TReDSPlatform) -> str:
        """Get base URL for the TReDS platform"""
        urls = {
            TReDSPlatform.RXIL: settings.TREDS_RXIL_API_URL or "https://api.rxil.in/v1",
            TReDSPlatform.M1XCHANGE: settings.TREDS_M1XCHANGE_API_URL or "https://api.m1xchange.com/v1",
            TReDSPlatform.INVOICEMART: settings.TREDS_INVOICEMART_API_URL or "https://api.invoicemart.com/v1",
        }
        return urls.get(platform, settings.TREDS_API_BASE_URL)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={
                    "User-Agent": "MoneyOps-TReDS-Client/1.0",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Generate HMAC signature for API authentication"""
        if not self.api_key:
            return ""
        message = f"{timestamp}{payload}"
        signature = hmac.new(
            self.api_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def _authenticate(self) -> str:
        """Authenticate with TReDS platform and get access token"""
        if not self.enabled:
            logger.warning("treds_api_disabled")
            raise RuntimeError("TReDS API is disabled. Set TREDS_ENABLED=True")

        if self._auth_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._auth_token

        client = await self._get_client()
        timestamp = str(int(time.time()))

        auth_payload = {
            "apiKey": settings.TREDS_API_KEY,
            "timestamp": timestamp,
        }

        try:
            response = await client.post(
                "/auth/token",
                json=auth_payload,
                headers={
                    "X-Request-Signature": self._generate_signature(json.dumps(auth_payload), timestamp)
                }
            )
            response.raise_for_status()
            data = response.json()

            self._auth_token = data.get("accessToken")
            expires_in = data.get("expiresIn", 3600)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

            logger.info("treds_authenticated", platform=self.platform)
            return self._auth_token

        except httpx.HTTPStatusError as e:
            logger.error("treds_auth_failed", status=e.response.status_code, error=str(e))
            raise RuntimeError(f"TReDS authentication failed: {e.response.status_code}")
        except Exception as e:
            logger.error("treds_auth_error", error=str(e))
            raise

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retries: int = 3
    ) -> TReDSResponse:
        """Make authenticated request to TReDS API with retry logic"""
        if not self.enabled:
            return TReDSResponse(
                success=False,
                message="TReDS API is disabled",
                error_code="TREDS_DISABLED"
            )

        for attempt in range(retries):
            try:
                token = await self._authenticate()
                client = await self._get_client()

                headers = {
                    "Authorization": f"Bearer {token}",
                    "X-Request-ID": f"moneyops-{int(time.time())}-{attempt}"
                }

                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    headers=headers
                )
                response.raise_for_status()

                result = response.json()
                return TReDSResponse(
                    success=True,
                    message=result.get("message", "Success"),
                    data=result.get("data")
                )

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 401:
                    self._auth_token = None
                    continue
                if status == 429 and attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.error("treds_request_failed", status=status, endpoint=endpoint)
                return TReDSResponse(
                    success=False,
                    message=f"HTTP {status}: {e.response.text}",
                    error_code=f"HTTP_{status}"
                )

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.error("treds_request_error", error=str(e), endpoint=endpoint)
                return TReDSResponse(
                    success=False,
                    message=str(e),
                    error_code="REQUEST_ERROR"
                )

        return TReDSResponse(
            success=False,
            message="Max retries exceeded",
            error_code="MAX_RETRIES"
        )

    async def get_discounting_rates(self, invoice_amount: float, tenure_days: int) -> DiscountingRateResponse:
        """
        Fetch current discounting rates from TReDS platform.
        Returns real-time rates based on invoice amount and tenure.
        """
        if not self.enabled:
            # Return estimated rates when API is disabled
            return DiscountingRateResponse(
                platform=self.platform,
                min_rate=8.0,
                max_rate=12.0,
                currency="INR",
                tenure_days=tenure_days,
                effective_date=datetime.now().isoformat(),
                is_available=False
            )

        response = await self._request(
            "GET",
            f"/rates?amount={invoice_amount}&tenure={tenure_days}"
        )

        if response.success and response.data:
            return DiscountingRateResponse(
                platform=self.platform,
                min_rate=response.data.get("minRate", 8.0),
                max_rate=response.data.get("maxRate", 12.0),
                currency=response.data.get("currency", "INR"),
                tenure_days=response.data.get("tenureDays", tenure_days),
                effective_date=response.data.get("effectiveDate", datetime.now().isoformat()),
                is_available=response.data.get("isAvailable", True)
            )

        # Fallback to estimated rates
        logger.warning("treds_rates_fallback", reason=response.message)
        return DiscountingRateResponse(
            platform=self.platform,
            min_rate=8.0,
            max_rate=12.0,
            currency="INR",
            tenure_days=tenure_days,
            effective_date=datetime.now().isoformat(),
            is_available=False
        )

    async def discount_invoice(
        self,
        request: InvoiceDiscountingRequest
    ) -> DiscountInvoiceResponse:
        """
        Submit invoice for discounting on TReDS platform.
        Returns transaction details with discount rate applied.
        """
        if not self.enabled:
            raise RuntimeError("TReDS API is disabled. Set TREDS_ENABLED=True")

        # Get current discounting rates
        due_date = datetime.strptime(request.due_date, "%Y-%m-%d")
        tenure_days = (due_date - datetime.now()).days
        rates = await self.get_discounting_rates(request.amount, tenure_days)

        payload = {
            "invoiceId": request.invoice_id,
            "invoiceNumber": request.invoice_number,
            "invoiceDate": request.invoice_date,
            "dueDate": request.due_date,
            "amount": request.amount,
            "clientName": request.client_name,
            "clientGstin": request.client_gstin,
            "supplierGstin": request.supplier_gstin,
            "description": request.description,
        }

        response = await self._request("POST", "/invoices/discount", data=payload)

        if response.success and response.data:
            status_str = response.data.get("status", "PROCESSING")
            try:
                status = DiscountingStatus(status_str)
            except ValueError:
                status = DiscountingStatus.PROCESSING

            return DiscountInvoiceResponse(
                transaction_id=response.data.get("transactionId", ""),
                invoice_id=request.invoice_id,
                original_amount=request.amount,
                discount_rate=response.data.get("discountRate", rates.min_rate),
                discounted_amount=response.data.get("discountedAmount", request.amount * (1 - rates.min_rate/100)),
                fee=response.data.get("fee", request.amount * rates.min_rate/100),
                status=status,
                platform=self.platform,
                created_at=response.data.get("createdAt", datetime.now().isoformat()),
                settlement_date=response.data.get("settlementDate")
            )

        raise RuntimeError(f"Invoice discounting failed: {response.message}")

    async def check_discounting_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check status of a discounting transaction"""
        if not self.enabled:
            return {"status": "UNKNOWN", "message": "TReDS API disabled"}

        response = await self._request("GET", f"/transactions/{transaction_id}/status")

        if response.success:
            return {
                "status": response.data.get("status", "UNKNOWN"),
                "transaction_id": transaction_id,
                "settlement_date": response.data.get("settlementDate"),
                "amount_disbursed": response.data.get("amountDisbursed"),
                "message": response.message
            }

        return {"status": "ERROR", "message": response.message}

    async def get_eligible_invoices(self, supplier_gstin: str) -> List[Dict[str, Any]]:
        """Get list of invoices eligible for discounting"""
        if not self.enabled:
            return []

        response = await self._request("GET", f"/invoices/eligible?gstin={supplier_gstin}")

        if response.success and response.data:
            return response.data.get("invoices", [])

        return []


# Singleton instance
treds_client = TReDSClient()
