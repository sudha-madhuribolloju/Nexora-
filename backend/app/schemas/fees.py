import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.fees import InvoiceStatus, PaymentMethod


# ─── Fee Structure Schemas ───────────────────────────────────────────────────

class FeeStructureBase(BaseModel):
    name: str
    description: Optional[str] = None
    amount: Decimal
    is_active: bool = True


class FeeStructureCreate(FeeStructureBase):
    school_id: uuid.UUID
    academic_year_id: Optional[uuid.UUID] = None


class FeeStructureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


class FeeStructureResponse(FeeStructureBase):
    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeeStructureListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[FeeStructureResponse]


# ─── Student Fee Invoice Schemas ─────────────────────────────────────────────

class InvoiceBase(BaseModel):
    title: str
    total_amount: Decimal
    due_date: Optional[datetime] = None


class InvoiceCreate(InvoiceBase):
    student_id: uuid.UUID
    school_id: uuid.UUID
    fee_structure_id: Optional[uuid.UUID] = None
    invoice_number: Optional[str] = None  # auto-generated if omitted


class InvoiceUpdate(BaseModel):
    title: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[datetime] = None


class InvoiceResponse(InvoiceBase):
    id: uuid.UUID
    student_id: uuid.UUID
    school_id: uuid.UUID
    fee_structure_id: Optional[uuid.UUID] = None
    invoice_number: str
    paid_amount: Decimal
    balance_due: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[InvoiceResponse]


# ─── Fee Payment Schemas ─────────────────────────────────────────────────────

class PaymentBase(BaseModel):
    amount_paid: Decimal
    payment_method: PaymentMethod = PaymentMethod.CASH
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    invoice_id: uuid.UUID
    paid_by: Optional[uuid.UUID] = None


class PaymentResponse(PaymentBase):
    id: uuid.UUID
    invoice_id: uuid.UUID
    paid_by: Optional[uuid.UUID] = None
    paid_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[PaymentResponse]


# ─── Financial Analytics Summary Schema ──────────────────────────────────────

class FinanceSummaryResponse(BaseModel):
    total_invoiced: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    overdue_count: int
    paid_invoices_count: int
    unpaid_invoices_count: int
