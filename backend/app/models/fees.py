"""
app/models/fees.py
───────────────────
FeeStructure, StudentFeeInvoice, and FeePayment ORM models.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Numeric, Enum, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.people import Student
    from app.models.school import School, AcademicYear


class InvoiceStatus(str, enum.Enum):
    UNPAID         = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID           = "paid"
    OVERDUE        = "overdue"
    CANCELLED      = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH          = "cash"
    CARD          = "card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE        = "online"
    CHECK         = "check"


class FeeStructure(Base):
    """
    Fee template or fee component (e.g., Tuition Fee Grade 10, Library Fee 2026).
    """
    __tablename__ = "fee_structures"
    __table_args__ = (
        Index("ix_fee_structures_school_id", "school_id"),
        Index("ix_fee_structures_name",      "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    academic_year_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    invoices: Mapped[List["StudentFeeInvoice"]] = relationship("StudentFeeInvoice", back_populates="fee_structure", cascade="all, delete-orphan")


class StudentFeeInvoice(Base):
    """
    Student fee invoice / bill instance.
    """
    __tablename__ = "student_fee_invoices"
    __table_args__ = (
        Index("ix_student_fee_invoices_student_id", "student_id"),
        Index("ix_student_fee_invoices_school_id",  "school_id"),
        Index("ix_student_fee_invoices_status",     "status"),
        Index("ix_student_fee_invoices_number",     "invoice_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    fee_structure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fee_structures.id", ondelete="SET NULL"), nullable=True)

    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus, name="invoicestatus"), default=InvoiceStatus.UNPAID, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    fee_structure: Mapped[Optional["FeeStructure"]] = relationship("FeeStructure", back_populates="invoices")
    payments: Mapped[List["FeePayment"]] = relationship("FeePayment", back_populates="invoice", cascade="all, delete-orphan")


class FeePayment(Base):
    """
    Payment transaction record for an invoice.
    """
    __tablename__ = "fee_payments"
    __table_args__ = (
        Index("ix_fee_payments_invoice_id", "invoice_id"),
        Index("ix_fee_payments_paid_by",    "paid_by"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("student_fee_invoices.id", ondelete="CASCADE"), nullable=False)
    paid_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="paymentmethod"), default=PaymentMethod.CASH, nullable=False)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice: Mapped["StudentFeeInvoice"] = relationship("StudentFeeInvoice", back_populates="payments")
