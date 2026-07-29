import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_12_notifications_full_flow() -> None:
    recipient_id = str(uuid.uuid4())

    # 1. Create Notifications across types
    notif_payload_1 = {
        "recipient_id": recipient_id,
        "title": "Assignment Released: Physics Homework 4",
        "message": "Physics Homework 4 is due on Friday at 11:59 PM.",
        "notification_type": "assignment",
        "action_url": "/assignments/1"
    }
    create_resp_1 = client.post("/api/v1/notifications/", json=notif_payload_1)
    assert create_resp_1.status_code == 201, create_resp_1.text
    notif_data_1 = create_resp_1.json()
    assert notif_data_1["title"] == "Assignment Released: Physics Homework 4"
    assert notif_data_1["is_read"] is False
    assert notif_data_1["status"] == "unread"
    notif_id_1 = notif_data_1["id"]

    notif_payload_2 = {
        "recipient_id": recipient_id,
        "title": "AI Completion: Lesson Plan Generated",
        "message": "Your requested AI lesson plan on Thermodynamics is ready.",
        "notification_type": "ai_completion"
    }
    create_resp_2 = client.post("/api/v1/notifications/", json=notif_payload_2)
    assert create_resp_2.status_code == 201
    notif_id_2 = create_resp_2.json()["id"]

    # 2. List Notifications & Verify Unread Count
    list_resp = client.get(f"/api/v1/notifications/?recipient_id={recipient_id}")
    assert list_resp.status_code == 200, list_resp.text
    list_data = list_resp.json()
    assert list_data["total"] == 2
    assert list_data["unread_count"] == 2

    # 3. Mark Single Notification as Read
    read_resp = client.put(f"/api/v1/notifications/{notif_id_1}/read")
    assert read_resp.status_code == 200, read_resp.text
    assert read_resp.json()["is_read"] is True
    assert read_resp.json()["status"] == "read"

    # 4. Archive Notification
    archive_resp = client.put(f"/api/v1/notifications/{notif_id_2}/archive")
    assert archive_resp.status_code == 200, archive_resp.text
    assert archive_resp.json()["status"] == "archived"

    # 5. Mark All Notifications Read
    mark_all_resp = client.put(f"/api/v1/notifications/read-all?user_id={recipient_id}")
    assert mark_all_resp.status_code == 200

    # 6. Delete Notification
    del_resp = client.delete(f"/api/v1/notifications/{notif_id_1}?user_id={recipient_id}")
    assert del_resp.status_code == 204

    # 7. List Notifications & Verify Status Filtering (Deleted excluded)
    list_after_del = client.get(f"/api/v1/notifications/?recipient_id={recipient_id}")
    assert list_after_del.status_code == 200
    assert list_after_del.json()["total"] == 1
