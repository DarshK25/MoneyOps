"""
gRPC Server for MoneyOps.
Implements the gRPC services defined in moneyops.proto.
Acts as a proxy to the HTTP backend if needed, or can be integrated directly.
"""
import asyncio
import grpc
from typing import Dict, Any, List
from datetime import datetime
import sys
from pathlib import Path

_GEN_DIR = Path(__file__).resolve().parent / "gen"
if str(_GEN_DIR) not in sys.path:
    sys.path.insert(0, str(_GEN_DIR))
from app.grpc.gen import moneyops_pb2, moneyops_pb2_grpc
from app.config import settings
from app.adapters.backend_adapter import get_backend_adapter
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _error(code: str, message: str) -> moneyops_pb2.ErrorResponse:
    return moneyops_pb2.ErrorResponse(code=code, message=message)


def _items(data):
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return data["data"]
        if isinstance(data.get("data"), dict):
            return _items(data["data"])
        if isinstance(data.get("content"), list):
            return data["content"]
        for key in ("clients", "invoices", "transactions", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _invoice_status(status: int) -> str:
    if status == moneyops_pb2.DRAFT:
        return "DRAFT"
    if status == moneyops_pb2.SENT:
        return "SENT"
    if status == moneyops_pb2.OVERDUE:
        return "OVERDUE"
    if status == moneyops_pb2.PAID:
        return "PAID"
    if status == moneyops_pb2.CANCELLED:
        return "CANCELLED"
    return ""


def _client_from_dict(client: Dict[str, Any]) -> moneyops_pb2.Client:
    name = client.get("name") or client.get("displayName") or client.get("company") or ""
    return moneyops_pb2.Client(
        id=str(client.get("id") or ""),
        display_name=str(name),
        backend_name=str(client.get("name") or name),
        email=str(client.get("email") or ""),
        status=str(client.get("status") or "ACTIVE"),
        org_id=str(client.get("orgId") or client.get("org_id") or ""),
    )


def _invoice_from_dict(invoice: Dict[str, Any]) -> moneyops_pb2.Invoice:
    items = []
    for item in invoice.get("items") or []:
        items.append(moneyops_pb2.InvoiceItem(
            description=str(item.get("description") or ""),
            quantity=float(item.get("quantity") or 0),
            unit_price=float(item.get("unitPrice") or item.get("rate") or 0),
            amount=float(item.get("amount") or item.get("lineTotal") or 0),
        ))
    return moneyops_pb2.Invoice(
        id=str(invoice.get("id") or ""),
        invoice_number=str(invoice.get("invoiceNumber") or invoice.get("invoice_number") or ""),
        client_id=str(invoice.get("clientId") or invoice.get("client_id") or ""),
        org_id=str(invoice.get("orgId") or invoice.get("org_id") or ""),
        total_amount=float(invoice.get("totalAmount") or invoice.get("total_amount") or 0),
        status=str(invoice.get("status") or ""),
        due_date=str(invoice.get("dueDate") or invoice.get("due_date") or ""),
        created_at=str(invoice.get("createdAt") or invoice.get("created_at") or ""),
        description=str(invoice.get("description") or invoice.get("notes") or ""),
        items=items,
    )


class OrganizationServicer(moneyops_pb2_grpc.OrganizationServiceServicer):
    """Implementation of OrganizationService."""

    async def GetOnboardingStatus(
        self,
        request: moneyops_pb2.UserIdRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetOnboardingStatusResponse:
        """Get onboarding status for a user ID."""
        try:
            backend = get_backend_adapter()
            resp = await backend.get_onboarding_status(request.user_id)
            if not resp.success:
                return moneyops_pb2.GetOnboardingStatusResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch onboarding status"),
                )
            data = resp.data or {}
            return moneyops_pb2.GetOnboardingStatusResponse(
                success=True,
                data=moneyops_pb2.OnboardingStatus(
                    onboarding_complete=bool(data.get("onboardingComplete") or data.get("onboarding_complete")),
                    org_id=str(data.get("orgId") or ""),
                    org_uuid=str(data.get("orgUuid") or ""),
                    organization_id=str(data.get("organizationId") or data.get("orgId") or ""),
                )
            )
        except Exception as e:
            logger.error("GetOnboardingStatus error", error=str(e))
            return moneyops_pb2.GetOnboardingStatusResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def GetOrganization(
        self,
        request: moneyops_pb2.OrgIdRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetOrganizationResponse:
        """Get organization by ID."""
        try:
            backend = get_backend_adapter()
            resp = await backend._request("GET", f"/api/org/{request.org_id}", org_id=request.org_id)
            if not resp.success:
                return moneyops_pb2.GetOrganizationResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch organization"),
                )
            data = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.GetOrganizationResponse(
                success=True,
                data=moneyops_pb2.Organization(
                    id=str(data.get("id") or request.org_id),
                    name=str(data.get("legalName") or data.get("tradeName") or data.get("name") or ""),
                    user_id=str(data.get("userId") or ""),
                    gst_number=str(data.get("gstin") or data.get("gstNumber") or ""),
                    status=str(data.get("status") or "ACTIVE"),
                    created_at=str(data.get("createdAt") or ""),
                )
            )
        except Exception as e:
            logger.error("GetOrganization error", error=str(e))
            return moneyops_pb2.GetOrganizationResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )


class ClientServicer(moneyops_pb2_grpc.ClientServiceServicer):
    """Implementation of ClientService."""

    async def GetClients(
        self,
        request: moneyops_pb2.GetClientsRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetClientsResponse:
        """Get clients for an organization."""
        try:
            backend = get_backend_adapter()
            clients = await backend.get_clients(request.org_id, limit=request.limit or 100)
            return moneyops_pb2.GetClientsResponse(
                success=True,
                clients=[_client_from_dict(client) for client in clients]
            )
        except Exception as e:
            logger.error("GetClients error", error=str(e))
            return moneyops_pb2.GetClientsResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def CreateClient(
        self,
        request: moneyops_pb2.CreateClientRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.CreateClientResponse:
        """Create a new client."""
        try:
            backend = get_backend_adapter()
            payload = {
                "name": request.name,
                "email": request.email,
                "phone": request.phone,
                "gstin": request.gst_number,
            }
            resp = await backend.create_client(request.org_id, None, payload)
            if not resp.success:
                return moneyops_pb2.CreateClientResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to create client"),
                )
            client = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.CreateClientResponse(
                success=True,
                client=_client_from_dict(client)
            )
        except Exception as e:
            logger.error("CreateClient error", error=str(e))
            return moneyops_pb2.CreateClientResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )


class InvoiceServicer(moneyops_pb2_grpc.InvoiceServiceServicer):
    """Implementation of InvoiceService."""

    async def GetInvoices(
        self,
        request: moneyops_pb2.GetInvoicesRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetInvoicesResponse:
        """Get invoices for an organization."""
        try:
            backend = get_backend_adapter()
            status = _invoice_status(request.status)
            resp = await backend.get_invoices(request.org_id, limit=request.limit or 100, status=status or None)
            if not resp.success:
                return moneyops_pb2.GetInvoicesResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch invoices"),
                )
            return moneyops_pb2.GetInvoicesResponse(
                success=True,
                invoices=[_invoice_from_dict(invoice) for invoice in _items(resp.data)]
            )
        except Exception as e:
            logger.error("GetInvoices error", error=str(e))
            return moneyops_pb2.GetInvoicesResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def GetInvoice(
        self,
        request: moneyops_pb2.GetInvoiceRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetInvoiceResponse:
        """Get a specific invoice."""
        try:
            backend = get_backend_adapter()
            resp = await backend._request("GET", f"/api/invoices/{request.invoice_id}", org_id=request.org_id)
            if not resp.success:
                return moneyops_pb2.GetInvoiceResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch invoice"),
                )
            invoice = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.GetInvoiceResponse(
                success=True,
                invoice=_invoice_from_dict(invoice)
            )
        except Exception as e:
            logger.error("GetInvoice error", error=str(e))
            return moneyops_pb2.GetInvoiceResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def CreateInvoice(
        self,
        request: moneyops_pb2.CreateInvoiceRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.CreateInvoiceResponse:
        """Create a new invoice."""
        try:
            backend = get_backend_adapter()
            payload = {
                "clientId": request.client_id,
                "totalAmount": request.total_amount,
                "dueDate": request.due_date,
                "description": request.description,
                "items": [
                    {
                        "description": item.description,
                        "quantity": item.quantity,
                        "rate": item.unit_price,
                        "amount": item.amount,
                    }
                    for item in request.items
                ],
                "source": "AI",
            }
            resp = await backend.create_invoice_direct(request.org_id, "", payload)
            if not resp.success:
                return moneyops_pb2.CreateInvoiceResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to create invoice"),
                )
            invoice = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.CreateInvoiceResponse(
                success=True,
                invoice=_invoice_from_dict(invoice)
            )
        except Exception as e:
            logger.error("CreateInvoice error", error=str(e))
            return moneyops_pb2.CreateInvoiceResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def MarkPaid(
        self,
        request: moneyops_pb2.MarkPaidRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.MarkPaidResponse:
        """Mark an invoice as paid."""
        try:
            backend = get_backend_adapter()
            resp = await backend._request(
                "POST",
                f"/api/invoices/{request.invoice_id}/payment",
                org_id=request.org_id,
                data={
                    "amount": request.amount,
                    "description": request.description,
                    "transactionDate": request.payment_date or datetime.utcnow().date().isoformat(),
                },
            )
            if not resp.success:
                return moneyops_pb2.MarkPaidResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to mark invoice paid"),
                )
            invoice_resp = await backend._request("GET", f"/api/invoices/{request.invoice_id}", org_id=request.org_id)
            invoice = invoice_resp.data if invoice_resp.success else {"id": request.invoice_id, "orgId": request.org_id, "status": "PAID"}
            if isinstance(invoice, dict):
                invoice = invoice.get("data", invoice)
            return moneyops_pb2.MarkPaidResponse(
                success=True,
                invoice=_invoice_from_dict(invoice)
            )
        except Exception as e:
            logger.error("MarkPaid error", error=str(e))
            return moneyops_pb2.MarkPaidResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )


class FinanceServicer(moneyops_pb2_grpc.FinanceServiceServicer):
    """Implementation of FinanceService."""

    async def GetFinanceMetrics(
        self,
        request: moneyops_pb2.FinanceMetricsRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetFinanceMetricsResponse:
        """Get finance metrics for an organization."""
        try:
            backend = get_backend_adapter()
            resp = await backend.get_finance_metrics(request.business_id or "1", request.org_id)
            if not resp.success:
                return moneyops_pb2.GetFinanceMetricsResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch finance metrics"),
                )
            data = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.GetFinanceMetricsResponse(
                success=True,
                data=moneyops_pb2.FinanceMetrics(
                    total_revenue=float(data.get("revenue") or data.get("totalRevenue") or data.get("totalIncome") or 0),
                    total_expenses=float(data.get("expenses") or data.get("totalExpenses") or data.get("totalExpense") or 0),
                    net_profit=float(data.get("netProfit") or 0),
                    cash_balance=float(data.get("cashBalance") or data.get("cash_balance") or 0),
                    outstanding_invoices=int(data.get("outstandingInvoices") or 0),
                    outstanding_amount=float(data.get("outstandingAmount") or 0),
                )
            )
        except Exception as e:
            logger.error("GetFinanceMetrics error", error=str(e))
            return moneyops_pb2.GetFinanceMetricsResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )

    async def GetFinancialSummary(
        self,
        request: moneyops_pb2.FinancialSummaryRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.GetFinancialSummaryResponse:
        """Get financial summary for an organization."""
        try:
            backend = get_backend_adapter()
            resp = await backend.get_financial_summary(request.org_id)
            if not resp.success:
                return moneyops_pb2.GetFinancialSummaryResponse(
                    success=False,
                    error=_error("BACKEND_ERROR", resp.error or "Failed to fetch financial summary"),
                )
            data = resp.data.get("data", resp.data) if isinstance(resp.data, dict) else {}
            return moneyops_pb2.GetFinancialSummaryResponse(
                success=True,
                data=moneyops_pb2.FinancialSummary(
                    total_income=float(data.get("totalIncome") or data.get("income") or 0),
                    total_expense=float(data.get("totalExpense") or data.get("expense") or 0),
                    recent_transactions=[],
                )
            )
        except Exception as e:
            logger.error("GetFinancialSummary error", error=str(e))
            return moneyops_pb2.GetFinancialSummaryResponse(
                success=False,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )


class NotificationServicer(moneyops_pb2_grpc.NotificationServiceServicer):
    """Implementation of NotificationService."""

    async def SendCollectionEmail(
        self,
        request: moneyops_pb2.SendCollectionEmailRequest,
        context: grpc.aio.ServicerContext
    ) -> moneyops_pb2.SendCollectionEmailResponse:
        """Send a collection email."""
        try:
            backend = get_backend_adapter()
            result = await backend.send_collection_email(
                invoice_id=request.invoice_id,
                client_email=request.client_email,
                client_name=request.client_name,
                invoice_number=request.invoice_number,
                amount=request.amount,
                due_date=request.due_date,
                org_id=request.org_id,
                tone=request.tone or "gentle",
            )
            if result.get("sent"):
                return moneyops_pb2.SendCollectionEmailResponse(
                    success=True,
                    sent=True,
                    recipient=request.client_email,
                )
            return moneyops_pb2.SendCollectionEmailResponse(
                success=False,
                sent=False,
                recipient=request.client_email,
                error=_error("BACKEND_ERROR", result.get("error") or "Failed to send email"),
            )
        except Exception as e:
            logger.error("SendCollectionEmail error", error=str(e))
            return moneyops_pb2.SendCollectionEmailResponse(
                success=False,
                sent=False,
                recipient=request.client_email,
                error=moneyops_pb2.ErrorResponse(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )


async def serve(port: int = None):
    """Start the gRPC server."""
    if port is None:
        from app.config import settings
        port = settings.GRPC_SERVER_PORT
    server = grpc.aio.server(options=[
        ('grpc.max_send_message_length', 50 * 1024 * 1024),
        ('grpc.max_receive_message_length', 50 * 1024 * 1024),
    ])

    # Register all services
    moneyops_pb2_grpc.add_OrganizationServiceServicer_to_server(
        OrganizationServicer(), server
    )
    moneyops_pb2_grpc.add_ClientServiceServicer_to_server(
        ClientServicer(), server
    )
    moneyops_pb2_grpc.add_InvoiceServiceServicer_to_server(
        InvoiceServicer(), server
    )
    moneyops_pb2_grpc.add_FinanceServiceServicer_to_server(
        FinanceServicer(), server
    )
    moneyops_pb2_grpc.add_NotificationServiceServicer_to_server(
        NotificationServicer(), server
    )

    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    logger.info("grpc_server_starting", port=port)

    await server.start()
    logger.info("grpc_server_started", port=port)

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("grpc_server_stopping")
        await server.stop(5)


if __name__ == "__main__":
    asyncio.run(serve())
