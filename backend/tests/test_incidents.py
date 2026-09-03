"""Tests for incident CRUD endpoints."""


def test_create_incident(client):
    payload = {
        "service": "payments-api",
        "severity": "HIGH",
        "description": "Test incident",
    }
    res = client.post("/api/v1/incidents", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "payments-api"
    assert data["severity"] == "HIGH"
    assert data["status"] == "ACTIVE"
    assert data["incident_id"].startswith("INC-")


def test_list_incidents_empty(client):
    res = client.get("/api/v1/incidents")
    assert res.status_code == 200
    assert res.json() == []


def test_list_incidents_after_create(client):
    client.post("/api/v1/incidents", json={"service": "svc-a", "severity": "LOW"})
    client.post("/api/v1/incidents", json={"service": "svc-b", "severity": "HIGH"})
    res = client.get("/api/v1/incidents")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_incident_by_id(client):
    create = client.post("/api/v1/incidents", json={"service": "svc-a", "severity": "MEDIUM"})
    inc_id = create.json()["incident_id"]

    res = client.get(f"/api/v1/incidents/{inc_id}")
    assert res.status_code == 200
    assert res.json()["incident_id"] == inc_id


def test_get_incident_not_found(client):
    res = client.get("/api/v1/incidents/INC-NOTEXIST")
    assert res.status_code == 404


def test_resolve_incident(client):
    create = client.post("/api/v1/incidents", json={"service": "svc-a", "severity": "HIGH"})
    inc_id = create.json()["incident_id"]

    res = client.patch(f"/api/v1/incidents/{inc_id}/resolve")
    assert res.status_code == 200

    # Verify status updated
    get = client.get(f"/api/v1/incidents/{inc_id}")
    assert get.json()["status"] == "RESOLVED"


def test_get_investigation_before_running(client):
    create = client.post("/api/v1/incidents", json={"service": "svc-a", "severity": "HIGH"})
    inc_id = create.json()["incident_id"]

    res = client.get(f"/api/v1/incidents/{inc_id}/investigation")
    assert res.status_code == 404
