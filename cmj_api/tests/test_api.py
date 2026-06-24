from fastapi.testclient import TestClient
from tests.conftest import build_test_cmj, FS


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_trial_success(client: TestClient):
    _, f = build_test_cmj()
    r = client.post("/trials/", json={"force_data": f.tolist(), "sample_rate": FS})
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "analyzed"
    assert data["metrics"]["jump_height_m"] > 0
    assert data["phases"]["flight"]["duration_ms"] > 0


def test_upload_trial_too_short(client: TestClient):
    r = client.post("/trials/", json={"force_data": [700.0] * 50, "sample_rate": FS})
    assert r.status_code == 422


def test_upload_trial_force_out_of_range(client: TestClient):
    r = client.post("/trials/", json={"force_data": [99999.0] * 200, "sample_rate": FS})
    assert r.status_code == 422


def test_get_trial_not_found(client: TestClient):
    r = client.get("/trials/does-not-exist")
    assert r.status_code == 404


def test_list_trials_by_athlete(client: TestClient):
    _, f = build_test_cmj()
    client.post("/trials/", json={
        "force_data": f.tolist(), "sample_rate": FS, "athlete_id": "athlete-001"
    })
    r = client.get("/trials/?athlete_id=athlete-001")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_trial_get_by_id(client: TestClient):
    _, f = build_test_cmj()
    post = client.post("/trials/", json={"force_data": f.tolist(), "sample_rate": FS})
    trial_id = post.json()["trial_id"]
    get = client.get(f"/trials/{trial_id}")
    assert get.status_code == 200
    assert get.json()["trial_id"] == trial_id
    assert get.json()["metrics"]["body_weight_n"] > 0
