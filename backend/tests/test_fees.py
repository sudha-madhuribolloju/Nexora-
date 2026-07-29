import pytest
import uuid

def test_fees_and_finance_management_full_flow(client):
    # 1. Setup School & Student IDs
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    # 2. Create Fee Structure
    structure_payload = {
        "name": "Tuition Fee Grade 10 - Academic Year 2026",
        "description": "Standard annual tuition fee covering core academic subjects.",
        "amount": 1500.00,
        "school_id": school_id,
        "is_active": True,
    }
    res = client.post("/fees/structures", json=structure_payload)
    assert res.status_code == 201, res.text
    struct_data = res.json()
    assert struct_data["name"] == "Tuition Fee Grade 10 - Academic Year 2026"
    structure_id = struct_data["id"]

    # 3. Get Fee Structure Detail
    res = client.get(f"/fees/structures/{structure_id}")
    assert res.status_code == 200
    assert res.json()["id"] == structure_id

    # 4. Update Fee Structure
    res = client.put(f"/fees/structures/{structure_id}", json={"description": "Updated tuition description."})
    assert res.status_code == 200
    assert res.json()["description"] == "Updated tuition description."

    # 5. List Fee Structures
    res = client.get(f"/fees/structures?school_id={school_id}")
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    # 6. Create Invoice for Student
    invoice_payload = {
        "title": "Fall Semester 2026 Tuition Invoice",
        "total_amount": 1500.00,
        "student_id": student_id,
        "school_id": school_id,
        "fee_structure_id": structure_id,
    }
    res = client.post("/fees/invoices", json=invoice_payload)
    assert res.status_code == 201, res.text
    inv_data = res.json()
    assert inv_data["title"] == "Fall Semester 2026 Tuition Invoice"
    assert inv_data["status"] == "unpaid"
    assert float(inv_data["paid_amount"]) == 0.0
    assert float(inv_data["balance_due"]) == 1500.0
    invoice_id = inv_data["id"]

    # 7. Get Invoice Detail
    res = client.get(f"/fees/invoices/{invoice_id}")
    assert res.status_code == 200
    assert res.json()["id"] == invoice_id

    # 8. List Invoices for Student
    res = client.get(f"/fees/invoices?student_id={student_id}")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # 9. Record Partial Payment ($500.00)
    payment1_payload = {
        "invoice_id": invoice_id,
        "amount_paid": 500.00,
        "payment_method": "card",
        "transaction_reference": "TXN-CARD-991823",
        "notes": "First installment paid by parent.",
    }
    res = client.post("/fees/payments", json=payment1_payload)
    assert res.status_code == 201, res.text
    pay1_data = res.json()
    assert float(pay1_data["amount_paid"]) == 500.00

    # Verify Invoice status updated to partially_paid
    res = client.get(f"/fees/invoices/{invoice_id}")
    assert res.status_code == 200
    inv_after_pay1 = res.json()
    assert inv_after_pay1["status"] == "partially_paid"
    assert float(inv_after_pay1["paid_amount"]) == 500.00
    assert float(inv_after_pay1["balance_due"]) == 1000.00

    # 10. List Payments for Invoice
    res = client.get(f"/fees/invoices/{invoice_id}/payments")
    assert res.status_code == 200
    payments_list = res.json()
    assert payments_list["total"] == 1

    # 11. Record Final Payment ($1000.00)
    payment2_payload = {
        "invoice_id": invoice_id,
        "amount_paid": 1000.00,
        "payment_method": "bank_transfer",
        "transaction_reference": "TXN-BANK-449102",
        "notes": "Final installment paid in full.",
    }
    res = client.post("/fees/payments", json=payment2_payload)
    assert res.status_code == 201, res.text

    # Verify Invoice status updated to paid
    res = client.get(f"/fees/invoices/{invoice_id}")
    assert res.status_code == 200
    inv_after_pay2 = res.json()
    assert inv_after_pay2["status"] == "paid"
    assert float(inv_after_pay2["paid_amount"]) == 1500.00
    assert float(inv_after_pay2["balance_due"]) == 0.00

    # 12. Verify Additional Payment Rejection on Fully Paid Invoice
    res = client.post("/fees/payments", json={
        "invoice_id": invoice_id,
        "amount_paid": 100.00,
        "payment_method": "cash"
    })
    assert res.status_code == 400

    # 13. Finance Analytics Summary
    res = client.get(f"/fees/summary?school_id={school_id}")
    assert res.status_code == 200, res.text
    summary = res.json()
    assert float(summary["total_invoiced"]) == 1500.00
    assert float(summary["total_collected"]) == 1500.00
    assert float(summary["total_outstanding"]) == 0.00
    assert summary["paid_invoices_count"] == 1

    # 14. Delete Invoice
    res = client.delete(f"/fees/invoices/{invoice_id}")
    assert res.status_code == 204

    # Verify deleted invoice returns 404
    res = client.get(f"/fees/invoices/{invoice_id}")
    assert res.status_code == 404

    # 15. Delete Fee Structure
    res = client.delete(f"/fees/structures/{structure_id}")
    assert res.status_code == 204

    # Verify deleted structure returns 404
    res = client.get(f"/fees/structures/{structure_id}")
    assert res.status_code == 404
