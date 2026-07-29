"""
Fees & Finance router — Fee structures, Student invoices, Payments, and Financial Summary.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.fees import InvoiceStatus
from app.services.fee_service import FeeService
from app.schemas.fees import (
    FeeStructureCreate, FeeStructureUpdate, FeeStructureResponse, FeeStructureListResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    PaymentCreate, PaymentResponse, PaymentListResponse,
    FinanceSummaryResponse,
)

router = APIRouter()


# ─── Financial Analytics Summary ──────────────────────────────────────────────

@router.get("/summary", response_model=FinanceSummaryResponse, summary="Get financial summary")
async def get_finance_summary(
    school_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get financial summary analytics (total invoiced, collected, outstanding, status counts).
    """
    return await FeeService.get_finance_summary(db, school_id)


# ─── Fee Structures ──────────────────────────────────────────────────────────

@router.get("/structures", response_model=FeeStructureListResponse, summary="List fee structures")
async def list_fee_structures(
    school_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve paginated fee structures.
    """
    total, items = await FeeService.list_fee_structures(db, school_id, skip, limit)
    return FeeStructureListResponse(total=total, skip=skip, limit=limit, data=items)


@router.post("/structures", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED, summary="Create fee structure")
async def create_fee_structure(
    data: FeeStructureCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new fee structure / category.
    """
    return await FeeService.create_fee_structure(db, data)


@router.get("/structures/{structure_id}", response_model=FeeStructureResponse, summary="Get fee structure detail")
async def get_fee_structure(
    structure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get fee structure by ID.
    """
    return await FeeService.get_fee_structure(db, structure_id)


@router.put("/structures/{structure_id}", response_model=FeeStructureResponse, summary="Update fee structure")
async def update_fee_structure(
    structure_id: uuid.UUID,
    data: FeeStructureUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update fee structure.
    """
    return await FeeService.update_fee_structure(db, structure_id, data)


@router.delete("/structures/{structure_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete fee structure")
async def delete_fee_structure(
    structure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete fee structure.
    """
    await FeeService.delete_fee_structure(db, structure_id)


# ─── Student Invoices ────────────────────────────────────────────────────────

@router.get("/invoices", response_model=InvoiceListResponse, summary="List student fee invoices")
async def list_invoices(
    student_id: Optional[uuid.UUID] = Query(None),
    school_id: Optional[uuid.UUID] = Query(None),
    invoice_status: Optional[InvoiceStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve paginated student fee invoices.
    """
    total, items = await FeeService.list_invoices(db, student_id, school_id, invoice_status, skip, limit)
    return InvoiceListResponse(total=total, skip=skip, limit=limit, data=items)


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, summary="Create student fee invoice")
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate a new fee invoice for a student.
    """
    return await FeeService.create_invoice(db, data)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, summary="Get invoice detail")
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get invoice details by ID.
    """
    return await FeeService.get_invoice(db, invoice_id)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse, summary="Update invoice")
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update invoice details.
    """
    return await FeeService.update_invoice(db, invoice_id, data)


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete invoice")
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete invoice.
    """
    await FeeService.delete_invoice(db, invoice_id)


# ─── Payments ────────────────────────────────────────────────────────────────

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, summary="Record fee payment")
async def record_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Record payment for an invoice and update invoice balance & status.
    """
    return await FeeService.record_payment(db, data)


@router.get("/invoices/{invoice_id}/payments", response_model=PaymentListResponse, summary="List payments for invoice")
async def list_payments_for_invoice(
    invoice_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all payment transactions for a specific invoice.
    """
    total, items = await FeeService.list_payments(db, invoice_id, skip, limit)
    return PaymentListResponse(total=total, skip=skip, limit=limit, data=items)
