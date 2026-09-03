"""Tests for the AI investigation pipeline."""
import pytest
from datetime import datetime, timedelta

from app.models.telemetry import MetricEvent, LogEvent, DeploymentEvent
from app.models.incident import Incident
from app.providers.deterministic import DeterministicInvestigator


# ────────────────────────────────────────────
# Deterministic investigator unit tests
# ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deployment_regression_scenario():
    """Deployment + DB spike + timeout logs → DB pool exhaustion."""
    evidence = {
        "deployments": [{"version": "v2.8.1", "minutes_before_incident": 2.0}],
        "metric_anomalies": [
            {"metric": "db_connections", "average": 98, "samples": 5},
            {"metric": "error_rate",     "average": 8.7, "samples": 5},
        ],
        "error_logs": [
            {"timestamp": "2026-09-02T02:09:20", "level": "ERROR", "message": "database connection timeout after 5000ms"},
            {"timestamp": "2026-09-02T02:09:45", "level": "ERROR", "message": "connection pool exhausted"},
        ],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    assert result.incident_summary["confidence_score"] >= 0.85
    assert "database" in result.incident_summary["primary_root_cause"].lower()
    assert any(h["status"] == "MOST_LIKELY" for h in result.evaluated_hypotheses)
    assert any(h["status"] == "REJECTED" and "cpu" in h["hypothesis_name"].lower()
               for h in result.evaluated_hypotheses)


@pytest.mark.asyncio
async def test_database_failure_scenario():
    """No deployment + DB refused → database server failure."""
    evidence = {
        "deployments": [],
        "metric_anomalies": [
            {"metric": "error_rate",     "average": 12.5, "samples": 3},
            {"metric": "latency_p95",    "average": 5200, "samples": 3},
        ],
        "error_logs": [
            {"timestamp": "2026-09-03T14:22:10", "level": "ERROR", "message": "database connection refused"},
            {"timestamp": "2026-09-03T14:22:30", "level": "ERROR", "message": "health check failed: database unreachable"},
        ],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    assert "database" in result.incident_summary["primary_root_cause"].lower()
    # Deployment regression must be rejected
    deploy_hypothesis = next(
        (h for h in result.evaluated_hypotheses if "deployment" in h["hypothesis_name"].lower()),
        None,
    )
    assert deploy_hypothesis is not None
    assert deploy_hypothesis["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_traffic_spike_scenario():
    """No deployment + CPU spike + error rate + latency → traffic saturation."""
    evidence = {
        "deployments": [],
        "metric_anomalies": [
            {"metric": "cpu_usage",   "average": 91, "samples": 4},
            {"metric": "error_rate",  "average": 5.3, "samples": 4},
            {"metric": "latency_p95", "average": 1800, "samples": 4},
        ],
        "error_logs": [
            {"timestamp": "2026-09-04T18:31:00", "level": "ERROR", "message": "worker thread pool saturated"},
        ],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    assert "saturation" in result.incident_summary["primary_root_cause"].lower() or \
           "traffic" in result.incident_summary["primary_root_cause"].lower()


@pytest.mark.asyncio
async def test_dependency_failure_scenario():
    """Dependency latency spike + payment gateway logs → external dependency."""
    evidence = {
        "deployments": [],
        "metric_anomalies": [
            {"metric": "dependency_latency", "average": 7200, "samples": 3},
            {"metric": "latency_p95",        "average": 8500, "samples": 3},
        ],
        "error_logs": [
            {"timestamp": "2026-09-05T09:18:20", "level": "ERROR", "message": "payment-gateway request timeout after 8000ms"},
            {"timestamp": "2026-09-05T09:19:00", "level": "ERROR", "message": "circuit breaker OPEN: payment-gateway"},
        ],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    assert "dependency" in result.incident_summary["primary_root_cause"].lower() or \
           "payment" in result.incident_summary["primary_root_cause"].lower()


@pytest.mark.asyncio
async def test_ai_safety_no_hallucination():
    """AI must only use evidence provided — never invent extra fields."""
    evidence = {
        "deployments": [],
        "metric_anomalies": [],
        "error_logs": [],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    # With no evidence, confidence must be low
    assert result.incident_summary["confidence_score"] < 0.6
    # Must not claim high confidence
    assert result.incident_summary["severity"] in ("LOW", "MEDIUM")


@pytest.mark.asyncio
async def test_ai_returns_structured_output():
    """AI result must conform to the required schema."""
    evidence = {
        "deployments": [{"version": "v1.0", "minutes_before_incident": 5}],
        "metric_anomalies": [{"metric": "error_rate", "average": 9, "samples": 3}],
        "error_logs": [{"timestamp": "2026-01-01T00:00:00", "level": "ERROR", "message": "timeout"}],
    }
    inv = DeterministicInvestigator()
    result = await inv.investigate(evidence)

    assert "title" in result.incident_summary
    assert "confidence_score" in result.incident_summary
    assert "primary_root_cause" in result.incident_summary
    assert isinstance(result.causal_narrative, str)
    assert len(result.causal_narrative) > 0
    assert isinstance(result.evaluated_hypotheses, list)
    assert isinstance(result.recommended_actions, list)


# ────────────────────────────────────────────
# End-to-end API flow test
# ────────────────────────────────────────────

def test_end_to_end_investigation_flow(client):
    """Full pipeline: ingest telemetry → create incident → investigate → read result."""
    # 1. Ingest deployment
    client.post("/api/v1/telemetry/deployments", json={
        "timestamp": "2026-09-02T02:07:00",
        "service": "payments-api",
        "version": "v2.8.1",
        "commit_sha": "abc123",
        "author": "alice@example.com",
        "environment": "production",
        "status": "success",
    })

    # 2. Ingest metric anomaly
    for val, ts in [(0.4, "2026-09-02T02:05:00"), (8.7, "2026-09-02T02:10:00")]:
        client.post("/api/v1/telemetry/metrics", json={
            "timestamp": ts,
            "service": "payments-api",
            "metric_name": "error_rate",
            "value": val,
            "unit": "percent",
        })

    for val, ts in [(42, "2026-09-02T02:05:00"), (98, "2026-09-02T02:10:00")]:
        client.post("/api/v1/telemetry/metrics", json={
            "timestamp": ts,
            "service": "payments-api",
            "metric_name": "db_connections",
            "value": val,
            "unit": "count",
        })

    # 3. Ingest error log
    client.post("/api/v1/telemetry/logs", json={
        "timestamp": "2026-09-02T02:09:20",
        "service": "payments-api",
        "level": "ERROR",
        "message": "database connection timeout after 5000ms",
    })
    client.post("/api/v1/telemetry/logs", json={
        "timestamp": "2026-09-02T02:09:45",
        "service": "payments-api",
        "level": "ERROR",
        "message": "connection pool exhausted: max 100 connections reached",
    })

    # 4. Create incident
    create_res = client.post("/api/v1/incidents", json={
        "service": "payments-api",
        "severity": "HIGH",
        "description": "Error rate spike after deployment",
    })
    assert create_res.status_code == 200
    inc_id = create_res.json()["incident_id"]

    # 5. Trigger investigation
    inv_res = client.post(f"/api/v1/incidents/{inc_id}/investigate")
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "completed"

    # 6. Read investigation result
    get_res = client.get(f"/api/v1/incidents/{inc_id}/investigation")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["root_cause"] is not None
    assert data["confidence_score"] is not None
    assert data["causal_narrative"] is not None

    # 7. Read timeline
    tl = client.get(f"/api/v1/incidents/{inc_id}/timeline")
    assert tl.status_code == 200

    # 8. Read evidence
    ev = client.get(f"/api/v1/incidents/{inc_id}/evidence")
    assert ev.status_code == 200
