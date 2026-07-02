"""
TReDS (Trade Receivables Discounting System) Schemas.

Pydantic models for TReDS API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TReDSPlatform(str, Enum):
    """Supported TReDS platforms in India"""
    RXIL = "rxil"
    M1XCHANGE = "m1xchange"
    INVOICEMART = "invoicemart"


class InvoiceStatus(str, Enum):
    """Invoice status in TReDS platform"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    DISCOUNTED = "DISCOUNTED"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"


class DiscountingStatus(str, Enum):
    """Discounting transaction status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InvoiceDiscountingRequest(BaseModel):
    """Request schema for invoice discounting on TReDS"""
    invoice_id: str = Field(..., description="Internal invoice ID")
    invoice_number: str = Field(..., description="Invoice number as per invoice")
    invoice_date: str = Field(..., description="Invoice date (YYYY-MM-DD)")
    due_date: str = Field(..., description="Invoice due date (YYYY-MM-DD)")
    amount: float = Field(..., ge=0, description="Invoice amount in INR")
    client_name: str = Field(..., description="Client/Buyer name")
    client_gstin: Optional[str] = Field(None, description="Client GSTIN")
    supplier_gstin: Optional[str] = Field(None, description="Supplier GSTIN")
    description: Optional[str] = Field(None, description="Invoice description")
    po_number: Optional[str] = Field(None, description="Purchase order number")


class DiscountingRateRequest(BaseModel):
    """Request for discounting rate inquiry"""
    invoice_amount: float = Field(..., ge=0, description="Invoice amount")
    tenure_days: int = Field(..., ge=1, le=180, description="Credit tenure in days")
    supplier_gstin: Optional[str] = Field(None, description="Supplier GSTIN")
    client_gstin: Optional[str] = Field(None, description="Client GSTIN")


class DiscountingRateResponse(BaseModel):
    """Response with discounting rates"""
    platform: TReDSPlatform = Field(..., description="TReDS platform name")
    min_rate: float = Field(..., description="Minimum discount rate (%)")
    max_rate: float = Field(..., description="Maximum discount rate (%)")
    currency: str = Field("INR", description="Currency code")
    tenure_days: int = Field(..., description="Tenure in days")
    effective_date: str = Field(..., description="Rate effective date")
    is_available: bool = Field(True, description="Whether platform is available")


class DiscountInvoiceResponse(BaseModel):
    """Response from successful invoice discounting"""
    transaction_id: str = Field(..., description="TReDS transaction ID")
    invoice_id: str = Field(..., description="Internal invoice ID")
    original_amount: float = Field(..., description="Original invoice amount")
    discount_rate: float = Field(..., description="Applied discount rate (%)")
    discounted_amount: float = Field(..., description="Amount after discount")
    fee: float = Field(..., description="Discount fee charged")
    status: DiscountingStatus = Field(..., description="Transaction status")
    platform: TReDSPlatform = Field(..., description="TReDS platform used")
    created_at: str = Field(..., description="Transaction creation timestamp")
    settlement_date: Optional[str] = Field(None, description="Expected settlement date")


class TReDSTransaction(BaseModel):
    """TReDS transaction record"""
    transaction_id: str
    invoice_id: str
    invoice_number: str
    client_name: str
    original_amount: float
    discounted_amount: float
    discount_rate: float
    fee: float
    status: DiscountingStatus
    platform: TReDSPlatform
    created_at: datetime
    settlement_date: Optional[datetime] = None
    remarks: Optional[str] = None


class EligibleInvoice(BaseModel):
    """Invoice eligible for TReDS discounting"""
    invoice_id: str
    invoice_number: str
    client_name: str
    amount: float
    invoice_date: str
    due_date: str
    days_until_due: int
    estimated_discount_rate: Optional[float] = None
    estimated_fee: Optional[float] = None


class TReDSPlatformStatus(BaseModel):
    """Status of TReDS platform connectivity"""
    platform: TReDSPlatform
    is_online: bool
    response_time_ms: Optional[float] = None
    last_checked: datetime
    error_message: Optional[str] = None
