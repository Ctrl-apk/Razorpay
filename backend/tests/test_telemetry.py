"""Tests for telemetry ingestion endpoints."""
from datetime import datetime


def test_ingest_metric_valid(client):
    payload = {
        "timestamp": "2026-09-02T02:10:00",
        "service": "payments-api",
        "metric_name": "error_rate",
        "value": 8.7,
        "unit": "percent",
        "labels": {"env": "production"},
    }
    res = client.post("/api/v1/telemetry/metrics", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "created_at" in data


def test_ingest_metric_missing_field(client):
    """Missing required field should return 422."""
    payload = {
        "timestamp": "2026-09-02T02:10:00",
        "service": "payments-api",
        # missing metric_name and value
    }
    res = client.post("/api/v1/telemetry/metrics", json=payload)
    assert res.status_code == 422


def test_ingest_log_valid(client):
    payload = {
        "timestamp": "2026-09-02T02:09:20",
        "service": "payments-api",
        "level": "ERROR",
        "message": "database connection timeout after 5000ms",
    }
    res = client.post("/api/v1/telemetry/logs", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data


def test_ingest_log_invalid_level_still_accepted(client):
    """Level is a free string — any value is accepted."""
    payload = {
        "timestamp": "2026-09-02T02:09:20",
        "service": "payments-api",
        "level": "TRACE",
        "message": "some trace message",
    }
    res = client.post("/api/v1/telemetry/logs", json=payload)
    assert res.status_code == 200


def test_ingest_deployment_valid(client):
    payload = {
        "timestamp": "2026-09-02T02:07:00",
        "service": "payments-api",
        "version": "v2.8.1",
        "commit_sha": "abc123",
        "author": "alice@company.com",
        "environment": "production",
        "status": "success",
    }
    res = client.post("/api/v1/telemetry/deployments", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data


def test_ingest_trace_valid(client):
    payload = {
        "timestamp": "2026-09-02T02:10:00",
        "service": "payments-api",
        "trace_id": "trace-001",
        "span_id": "span-001",
        "operation": "POST /payments",
        "duration_ms": 920.5,
        "status": "error",
    }
    res = client.post("/api/v1/telemetry/traces", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
