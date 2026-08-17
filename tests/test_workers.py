from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_create_worker(client: TestClient):
    response = client.post("/workers", json={"name": "Jamie Lee", "role": "Cook"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Jamie Lee"
    assert body["role"] == "Cook"
    assert "id" in body
def test_update_worker(client: TestClient):
    create_res = client.post("/workers", json={"name": "Jamie Lee", "role": "Cook"})
    worker_id = create_res.json()["id"]

    update_res = client.put(f"/workers/{worker_id}", json={"name": "Jamie Lee", "role": "Head Chef"})
    assert update_res.status_code == 200
    
    body = update_res.json()
    assert body["id"] == worker_id
    assert body["role"] == "Head Chef"


def test_update_worker_not_found(client: TestClient):
    response = client.put("/workers/9999", json={"name": "Nobody", "role": "Ghost"})
    assert response.status_code == 404


def test_create_worker_requires_name(client: TestClient):
    response = client.post("/workers", json={"name": "", "role": "Cook"})
    assert response.status_code == 422


def test_create_worker_sanitizes_name(client: TestClient):
    response = client.post("/workers", json={"name": "Alice   Rivera", "role": "Cook"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alice Rivera"


def test_list_workers(client: TestClient):
    client.post("/workers", json={"name": "Jamie Lee", "role": "Cook"})
    client.post("/workers", json={"name": "Sam Osei", "role": "Cashier"})

    response = client.get("/workers")
    assert response.status_code == 200
    names = {w["name"] for w in response.json()}
    assert names == {"Jamie Lee", "Sam Osei"}


def test_get_worker_not_found(client: TestClient):
    response = client.get("/workers/999")
    assert response.status_code == 404


def test_get_worker_with_matching_role(client: TestClient):
    client.post("/workers", json={"name": "Jamie Lee", "role": "Cook"})
    client.post("/workers", json={"name": "Sam Osei", "role": "Cashier"})

    response = client.get("/workers?role=Cashier")
    names = {w["name"] for w in response.json()}
    assert names == {"Sam Osei"}


def test_get_worker_with_no_matching_role(client: TestClient):
    client.post("/workers", json={"name": "Jamie Lee", "role": "Cook"})
    client.post("/workers", json={"name": "Sam Osei", "role": "Cashier"})
    
    response = client.get("/workers?role=Owner")
    names = {w["name"] for w in response.json()}
    assert names == set()

def test_get_worker_next_shift(client: TestClient):
    # Create worker
    worker_res = client.post(
        "/workers",
        json={"name": "Jamie Lee", "role": "Cook"},
    )
    worker_id = worker_res.json()["id"]

    # Create upcoming shift
    now = datetime.now()
    shift_res = client.post(
        "/shifts",
        json={
            "worker_id": worker_id,
            "start_time": (now + timedelta(hours=2)).isoformat(),
            "end_time": (now + timedelta(hours=10)).isoformat(),
        },
    )

    assert shift_res.status_code == 201

    # Get next shift
    response = client.get(f"/workers/{worker_id}/next-shift")

    assert response.status_code == 200

    body = response.json()

    assert body["worker_id"] == worker_id
    assert "start_time" in body
    assert "end_time" in body
    assert "id" in body

def test_get_worker_next_shift_with_only_past_shifts(client: TestClient):
    # Create worker
    worker_res = client.post(
        "/workers",
        json={"name": "Sam Osei", "role": "Cashier"},
    )
    worker_id = worker_res.json()["id"]

    # Create past shift
    now = datetime.now()

    shift_res = client.post(
        "/shifts",
        json={
            "worker_id": worker_id,
            "start_time": (now - timedelta(hours=10)).isoformat(),
            "end_time": (now - timedelta(hours=2)).isoformat(),
        },
    )

    assert shift_res.status_code == 201

    # Get next shift
    response = client.get(f"/workers/{worker_id}/next-shift")

    assert response.status_code == 200

    # Worker exists but has no upcoming shifts
    assert response.json() is None


def test_get_worker_next_shift_not_found(client: TestClient):
    response = client.get("/workers/99999/next-shift")

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Worker not found"