import pytest
import uuid

def test_system_notifications_full_flow(client):
    # 1. Register Recipient & Sender Users
    recipient_res = client.post("/api/v1/auth/register", json={
        "email": "notif_recipient@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert recipient_res.status_code == 201, recipient_res.text
    recipient_id = recipient_res.json()["id"]

    sender_res = client.post("/api/v1/auth/register", json={
        "email": "notif_sender@example.com",
        "password": "Password123!",
        "role": "Admin"
    })
    assert sender_res.status_code == 201
    sender_id = sender_res.json()["id"]

    # 2. Create Notification 1
    notif1_payload = {
        "recipient_id": recipient_id,
        "title": "Midterm Examination Schedule",
        "message": "Physics Midterm examination will commence on Monday at 09:00 AM.",
        "notification_type": "announcement",
        "action_url": "/exams/physics-midterm",
    }
    res = client.post(f"/notifications/?sender_id={sender_id}", json=notif1_payload)
    assert res.status_code == 201, res.text
    notif1 = res.json()
    assert notif1["title"] == "Midterm Examination Schedule"
    assert notif1["is_read"] is False
    notif1_id = notif1["id"]

    # 3. Create Notification 2
    notif2_payload = {
        "recipient_id": recipient_id,
        "title": "Assignment Graded",
        "message": "Your submission for Homework 1 has been graded.",
        "notification_type": "info",
    }
    res = client.post(f"/notifications/?sender_id={sender_id}", json=notif2_payload)
    assert res.status_code == 201, res.text
    notif2_id = res.json()["id"]

    # 4. List Notifications for Recipient
    res = client.get(f"/notifications/?recipient_id={recipient_id}")
    assert res.status_code == 200, res.text
    list_data = res.json()
    assert list_data["total"] == 2
    assert list_data["unread_count"] == 2

    # 5. List Unread Only
    res = client.get(f"/notifications/?recipient_id={recipient_id}&unread_only=true")
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # 6. Mark Notification 1 as read
    res = client.put(f"/notifications/{notif1_id}/read?user_id={recipient_id}")
    assert res.status_code == 200, res.text
    read_notif = res.json()
    assert read_notif["is_read"] is True
    assert read_notif["read_at"] is not None

    # 7. List Notifications after marking 1 as read
    res = client.get(f"/notifications/?recipient_id={recipient_id}")
    assert res.status_code == 200
    assert res.json()["unread_count"] == 1

    # 8. Mark all remaining notifications as read
    res = client.put(f"/notifications/read-all?user_id={recipient_id}")
    assert res.status_code == 200, res.text

    # 9. Verify unread count is now 0
    res = client.get(f"/notifications/?recipient_id={recipient_id}")
    assert res.status_code == 200
    assert res.json()["unread_count"] == 0

    # 10. Get single notification detail
    res = client.get(f"/notifications/{notif1_id}")
    assert res.status_code == 200
    assert res.json()["id"] == notif1_id

    # 11. Delete Notification 1
    res = client.delete(f"/notifications/{notif1_id}?user_id={recipient_id}")
    assert res.status_code == 204

    # 12. Verify deleted notification returns 404
    res = client.get(f"/notifications/{notif1_id}")
    assert res.status_code == 404
