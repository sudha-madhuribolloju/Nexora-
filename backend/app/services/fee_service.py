"""
Fee Service — Business logic for fee structures, student invoices, payments, and financial analytics.
"""
import uuid
import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, status

from app.models.fees import FeeStructure, StudentFeeInvoice, FeePayment, InvoiceStatus
from app.schemas.fees import (
    FeeStructureCreate, FeeStructureUpdate,
    InvoiceCreate, InvoiceUpdate,
    PaymentCreate, FinanceSummaryResponse
)


def _generate_invoice_number() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand_suffix = random.randint(1000, 9999)
    return f"INV-{timestamp}-{rand_suffix}"


class FeeService:

    # ─── Fee Structures ──────────────────────────────────────────────────────

    @staticmethod
    async def create_fee_structure(
        db: AsyncSession, data: FeeStructureCreate
    ) -> FeeStructure:
        structure = FeeStructure(**data.model_dump())
        db.add(structure)
        await db.commit()
        await db.refresh(structure)
        return structure

    @staticmethod
    async def list_fee_structures(
        db: AsyncSession,
        school_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[int, List[FeeStructure]]:
        q = select(FeeStructure)
        if school_id:
            q = q.where(FeeStructure.school_id == school_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        items = (await db.execute(
            q.order_by(FeeStructure.created_at.desc()).offset(skip).limit(limit)
        )).scalars().all()
        return total, list(items)

    @staticmethod
    async def get_fee_structure(db: AsyncSession, structure_id: uuid.UUID) -> FeeStructure:
        res = await db.execute(select(FeeStructure).where(FeeStructure.id == structure_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee structure not found")
        return item

    @staticmethod
    async def update_fee_structure(
        db: AsyncSession, structure_id: uuid.UUID, data: FeeStructureUpdate
    ) -> FeeStructure:
        item = await FeeService.get_fee_structure(db, structure_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_fee_structure(db: AsyncSession, structure_id: uuid.UUID) -> None:
        item = await FeeService.get_fee_structure(db, structure_id)
        await db.delete(item)
        await db.commit()

    # ─── Student Invoices ────────────────────────────────────────────────────

    @staticmethod
    async def create_invoice(
        db: AsyncSession, data: InvoiceCreate
    ) -> StudentFeeInvoice:
        inv_number = data.invoice_number or _generate_invoice_number()
        payload = data.model_dump(exclude={"invoice_number"})
        
        total_amt = data.total_amount
        invoice = StudentFeeInvoice(
            **payload,
            invoice_number=inv_number,
            paid_amount=Decimal("0.00"),
            balance_due=total_amt,
            status=InvoiceStatus.UNPAID
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice

    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        student_id: Optional[uuid.UUID] = None,
        school_id: Optional[uuid.UUID] = None,
        invoice_status: Optional[InvoiceStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[int, List[StudentFeeInvoice]]:
        q = select(StudentFeeInvoice)
        if student_id:
            q = q.where(StudentFeeInvoice.student_id == student_id)
        if school_id:
            q = q.where(StudentFeeInvoice.school_id == school_id)
        if invoice_status:
            q = q.where(StudentFeeInvoice.status == invoice_status)
            
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        items = (await db.execute(
            q.order_by(StudentFeeInvoice.created_at.desc()).offset(skip).limit(limit)
        )).scalars().all()
        return total, list(items)

    @staticmethod
    async def get_invoice(db: AsyncSession, invoice_id: uuid.UUID) -> StudentFeeInvoice:
        res = await db.execute(select(StudentFeeInvoice).where(StudentFeeInvoice.id == invoice_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return item

    @staticmethod
    async def update_invoice(
        db: AsyncSession, invoice_id: uuid.UUID, data: InvoiceUpdate
    ) -> StudentFeeInvoice:
        item = await FeeService.get_invoice(db, invoice_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        # Recalculate balance_due if total_amount changed
        if data.total_amount is not None:
            item.balance_due = max(Decimal("0.00"), item.total_amount - item.paid_amount)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_invoice(db: AsyncSession, invoice_id: uuid.UUID) -> None:
        item = await FeeService.get_invoice(db, invoice_id)
        await db.delete(item)
        await db.commit()

    # ─── Payments ────────────────────────────────────────────────────────────

    @staticmethod
    async def record_payment(
        db: AsyncSession, data: PaymentCreate
    ) -> FeePayment:
        invoice = await FeeService.get_invoice(db, data.invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice is already fully paid")
        if data.amount_paid <= Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be greater than zero")

        payment = FeePayment(**data.model_dump())
        db.add(payment)

        # Update invoice payment fields
        invoice.paid_amount += data.amount_paid
        invoice.balance_due = max(Decimal("0.00"), invoice.total_amount - invoice.paid_amount)
        if invoice.balance_due == Decimal("0.00"):
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        await db.commit()
        await db.refresh(payment)
        await db.refresh(invoice)
        return payment

    @staticmethod
    async def list_payments(
        db: AsyncSession, invoice_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[int, List[FeePayment]]:
        q = select(FeePayment).where(FeePayment.invoice_id == invoice_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        payments = (await db.execute(
            q.order_by(FeePayment.paid_at.desc()).offset(skip).limit(limit)
        )).scalars().all()
        return total, list(payments)

    # ─── Financial Analytics Summary ──────────────────────────────────────────

    @staticmethod
    async def get_finance_summary(
        db: AsyncSession, school_id: Optional[uuid.UUID] = None
    ) -> FinanceSummaryResponse:
        q = select(StudentFeeInvoice)
        if school_id:
            q = q.where(StudentFeeInvoice.school_id == school_id)

        invoices = (await db.execute(q)).scalars().all()

        total_invoiced = sum(i.total_amount for i in invoices) if invoices else Decimal("0.00")
        total_collected = sum(i.paid_amount for i in invoices) if invoices else Decimal("0.00")
        total_outstanding = sum(i.balance_due for i in invoices) if invoices else Decimal("0.00")

        overdue_count = sum(1 for i in invoices if i.status == InvoiceStatus.OVERDUE)
        paid_count = sum(1 for i in invoices if i.status == InvoiceStatus.PAID)
        unpaid_count = sum(1 for i in invoices if i.status == InvoiceStatus.UNPAID)

        return FinanceSummaryResponse(
            total_invoiced=total_invoiced,
            total_collected=total_collected,
            total_outstanding=total_outstanding,
            overdue_count=overdue_count,
            paid_invoices_count=paid_count,
            unpaid_invoices_count=unpaid_count,
        )
