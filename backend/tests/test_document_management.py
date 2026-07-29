import io
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_6_document_management_full_flow() -> None:
    uploader_id = str(uuid.uuid4())

    # 1. Upload valid PDF document
    pdf_bytes = b"%PDF-1.4 sample PDF content for testing document management"
    upload_resp = client.post(
        f"/api/v1/documents/upload?uploader_id={uploader_id}",
        files={"file": ("quantum_physics.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Quantum Physics Notes", "category": "course_material"}
    )
    assert upload_resp.status_code == 201, upload_resp.text
    doc_data = upload_resp.json()
    assert doc_data["title"] == "Quantum Physics Notes"
    assert doc_data["version"] == 1
    doc_id = doc_data["id"]

    # 2. Upload valid DOCX document
    docx_bytes = b"PK\x03\x04 sample Word document content"
    docx_resp = client.post(
        f"/api/v1/documents/upload?uploader_id={uploader_id}",
        files={"file": ("lab_report.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"title": "Chemistry Lab Report", "category": "assignment"}
    )
    assert docx_resp.status_code == 201, docx_resp.text

    # 3. Duplicate Detection Check (Uploading identical content returns existing document)
    dup_resp = client.post(
        f"/api/v1/documents/upload?uploader_id={uploader_id}",
        files={"file": ("quantum_physics_copy.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Duplicate Quantum Physics", "category": "course_material"}
    )
    assert dup_resp.status_code == 201
    assert dup_resp.json()["id"] == doc_id

    # 4. Search Documents
    search_resp = client.get("/api/v1/documents/search?q=Quantum")
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert search_results["total"] >= 1
    assert search_results["data"][0]["id"] == doc_id

    # 5. Preview Document
    preview_resp = client.get(f"/api/v1/documents/{doc_id}/preview")
    assert preview_resp.status_code == 200
    assert preview_resp.json()["title"] == "Quantum Physics Notes"
    assert preview_resp.json()["version"] == 1

    # 6. Replace Document File (Increments Version to 2)
    new_pdf_bytes = b"%PDF-1.4 updated v2 PDF content for quantum physics"
    replace_resp = client.put(
        f"/api/v1/documents/{doc_id}/replace?uploader_id={uploader_id}",
        files={"file": ("quantum_physics_v2.pdf", new_pdf_bytes, "application/pdf")}
    )
    assert replace_resp.status_code == 200, replace_resp.text
    updated_doc = replace_resp.json()
    assert updated_doc["version"] == 2
    assert updated_doc["file_name"] == "quantum_physics_v2.pdf"

    # 7. Download Document (Redirects)
    download_resp = client.get(f"/api/v1/documents/{doc_id}/download", follow_redirects=False)
    assert download_resp.status_code == 302
    assert download_resp.headers["location"] == "/uploads/quantum_physics_v2.pdf"

    # 8. Validation Rejection: Unsupported file extension
    bad_ext_resp = client.post(
        f"/api/v1/documents/upload?uploader_id={uploader_id}",
        files={"file": ("malicious.exe", b"MZ malicious executable", "application/x-msdownload")},
        data={"title": "Bad File"}
    )
    assert bad_ext_resp.status_code == 400

    # 9. Delete Document
    del_resp = client.delete(f"/api/v1/documents/{doc_id}?user_id={uploader_id}")
    assert del_resp.status_code == 204

    # 10. Verify Deleted Document returns 404
    get_del_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert get_del_resp.status_code == 404
