"""Tests for the temporal correlation engine."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import TestingSessionLocal

from app.models.telemetry import MetricEvent, LogEvent, DeploymentEvent
from app.services.correlation_engine import CorrelationEngine


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    from app.database import Base
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = session.__class__(bind=engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_deployment_correlation_within_window(client, db):
    """Deployment within 15 minutes should be correlated."""
    incident_time = datetime(2026, 9, 2, 2, 9, 0)
    deploy_time   = datetime(2026, 9, 2, 2, 7, 0)

    db.add(DeploymentEvent(
        timestamp=deploy_time,
        service="payments-api",
        version="v2.8.1",
        commit_sha="abc123",
        environment="production",
        status="success",
    ))
    db.commit()

    engine = CorrelationEngine(db)
    result = engine.correlate_events(incident_time, "payments-api")

    assert len(result["deployments"]) == 1
    assert result["deployments"][0]["version"] == "v2.8.1"


def test_deployment_outside_window_not_correlated(client, db):
    """Deployment older than 15 minutes should NOT be correlated."""
    incident_time = datetime(2026, 9, 2, 2, 9, 0)
    old_deploy    = datetime(2026, 9, 2, 1, 30, 0)  # 39 minutes before

    db.add(DeploymentEvent(
        timestamp=old_deploy,
        service="payments-api",
        version="v2.0.0",
        environment="production",
        status="success",
    ))
    db.commit()

    engine = CorrelationEngine(db)
    result = engine.correlate_events(incident_time, "payments-api")
    assert len(result["deployments"]) == 0


def test_different_service_deployment_not_correlated(client, db):
    """Deployment for a different service should NOT be correlated."""
    incident_time = datetime(2026, 9, 2, 2, 9, 0)
    deploy_time   = datetime(2026, 9, 2, 2, 7, 0)

    db.add(DeploymentEvent(
        timestamp=deploy_time,
        service="other-service",   # different service
        version="v1.0.0",
        environment="production",
        status="success",
    ))
    db.commit()

    engine = CorrelationEngine(db)
    result = engine.correlate_events(incident_time, "payments-api")
    assert len(result["deployments"]) == 0


def test_error_logs_within_window_correlated(client, db):
    """Error logs within the window should be included."""
    incident_time = datetime(2026, 9, 2, 2, 9, 0)

    db.add(LogEvent(
        timestamp=datetime(2026, 9, 2, 2, 9, 20),
        service="payments-api",
        level="ERROR",
        message="database connection timeout",
    ))
    db.add(LogEvent(
        timestamp=datetime(2026, 9, 2, 2, 9, 45),
        service="payments-api",
        level="WARN",
        message="retrying connection",
    ))
    db.commit()

    engine = CorrelationEngine(db)
    result = engine.correlate_events(incident_time, "payments-api")
    assert len(result["log_errors"]) == 2


def test_timeline_sorted_chronologically(client, db):
    """Timeline events should be sorted by timestamp."""
    incident_time = datetime(2026, 9, 2, 2, 9, 0)

    db.add(LogEvent(timestamp=datetime(2026, 9, 2, 2, 10, 0), service="payments-api", level="ERROR", message="error2"))
    db.add(LogEvent(timestamp=datetime(2026, 9, 2, 2,  9, 0), service="payments-api", level="ERROR", message="error1"))
    db.add(DeploymentEvent(timestamp=datetime(2026, 9, 2, 2, 7, 0), service="payments-api", version="v2.8.1", environment="production", status="success"))
    db.commit()

    engine = CorrelationEngine(db)
    result = engine.correlate_events(incident_time, "payments-api")
    tl = result["timeline"]
    timestamps = [e["timestamp"] for e in tl]
    assert timestamps == sorted(timestamps)
