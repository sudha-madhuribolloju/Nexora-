import pytest
import uuid

def test_documents_and_knowledge_base_full_flow(client):
    # ─── PART 1: Document Management ──────────────────────────────────────────
    
    # 1. Create Document metadata
    doc_payload = {
        "title": "Quantum Physics Lecture Notes",
        "description": "Comprehensive notes covering quantum states and operators.",
        "category": "course_material",
        "file_name": "quantum_notes.pdf",
        "file_url": "/uploads/quantum_notes.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 1048576,
        "is_public": True,
    }
    uploader_id = str(uuid.uuid4())
    res = client.post(f"/documents/?uploader_id={uploader_id}", json=doc_payload)
    assert res.status_code == 201, res.text
    doc_data = res.json()
    assert doc_data["title"] == "Quantum Physics Lecture Notes"
    doc_id = doc_data["id"]

    # 2. Get Document metadata by ID
    res = client.get(f"/documents/{doc_id}")
    assert res.status_code == 200
    assert res.json()["file_name"] == "quantum_notes.pdf"

    # 3. List Documents
    res = client.get("/documents/")
    assert res.status_code == 200
    docs_list = res.json()
    assert docs_list["total"] >= 1

    # 4. Index Document text into vector store
    res = client.post("/documents/index", data={"document_id": doc_id})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "success"

    # 5. Delete Document
    res = client.delete(f"/documents/{doc_id}?user_id={uploader_id}")
    assert res.status_code == 204

    # 6. Verify deleted Document returns 404
    res = client.get(f"/documents/{doc_id}")
    assert res.status_code == 404

    # ─── PART 2: Knowledge Base Articles ──────────────────────────────────────
    
    # 7. Create KB Article
    article_payload = {
        "title": "Physics Laboratory Safety Protocols",
        "content": "All students must wear protective goggles and follow instructor guidance.",
        "summary": "Mandatory safety rules for physics labs.",
        "category": "Lab Safety",
        "tags": ["physics", "safety", "lab"],
        "is_featured": True,
    }
    author_id = str(uuid.uuid4())
    res = client.post(f"/knowledge-base/?author_id={author_id}", json=article_payload)
    assert res.status_code == 201, res.text
    article_data = res.json()
    assert article_data["title"] == "Physics Laboratory Safety Protocols"
    assert article_data["status"] == "draft"
    article_id = article_data["id"]

    # 8. Get Article (increments view count)
    res = client.get(f"/knowledge-base/{article_id}")
    assert res.status_code == 200
    assert res.json()["views"] == 1

    # 9. Like Article
    res = client.post(f"/knowledge-base/{article_id}/like")
    assert res.status_code == 200
    assert res.json()["likes"] == 1

    # 10. Publish Article
    res = client.put(f"/knowledge-base/{article_id}", json={"status": "published"})
    assert res.status_code == 200, res.text
    published_article = res.json()
    assert published_article["status"] == "published"
    assert published_article["published_at"] is not None

    # 11. Search KB Articles
    res = client.get("/knowledge-base/search?q=Safety")
    assert res.status_code == 200, res.text
    search_results = res.json()
    assert search_results["total"] == 1
    assert search_results["data"][0]["id"] == article_id

    # 12. List KB Articles
    res = client.get("/knowledge-base/")
    assert res.status_code == 200
    articles_list = res.json()
    assert articles_list["total"] >= 1

    # 13. Delete KB Article
    res = client.delete(f"/knowledge-base/{article_id}")
    assert res.status_code == 204

    # 14. Verify deleted Article returns 404
    res = client.get(f"/knowledge-base/{article_id}")
    assert res.status_code == 404
