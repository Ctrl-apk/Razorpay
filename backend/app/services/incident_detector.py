from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.telemetry import MetricEvent
from ..models.incident import Incident
from uuid import uuid4


class IncidentDetector:
    """Deterministic incident detector based on configurable thresholds."""

    def __init__(self, db: Session):
        self.db = db
        self.error_rate_threshold    = 2.0
        self.latency_threshold       = 2.0
        self.db_connection_threshold = 1.5

    def detect_anomalies(self, service: str, window_minutes: int = 10):
        now            = datetime.utcnow()
        baseline_end   = now - timedelta(minutes=window_minutes)
        baseline_start = now - timedelta(minutes=window_minutes * 2)

        baseline = self._avg_metrics(service, baseline_start, baseline_end)
        current  = self._avg_metrics(service, baseline_end, now)

        anomalies      = []
        trigger_metrics = {}

        if "error_rate" in baseline and "error_rate" in current:
            b, c = baseline["error_rate"], current["error_rate"]
            if b > 0 and c > b * self.error_rate_threshold:
                anomalies.append("error_rate")
                trigger_metrics["error_rate"] = {"baseline": b, "current": c, "ratio": c / b}

        if "latency_p95" in baseline and "latency_p95" in current:
            b, c = baseline["latency_p95"], current["latency_p95"]
            if b > 0 and c > b * self.latency_threshold:
                anomalies.append("latency_p95")
                trigger_metrics["latency_p95"] = {"baseline": b, "current": c, "ratio": c / b}

        if "db_connections" in baseline and "db_connections" in current:
            b, c = baseline["db_connections"], current["db_connections"]
            if b > 0 and c > b * self.db_connection_threshold:
                anomalies.append("db_connections")
                trigger_metrics["db_connections"] = {"baseline": b, "current": c, "ratio": c / b}

        return anomalies, trigger_metrics, baseline_end

    def _avg_metrics(self, service: str, start: datetime, end: datetime):
        metrics = {}
        for name in ["error_rate", "latency_p95", "db_connections"]:
            rows = self.db.query(MetricEvent).filter(
                and_(
                    MetricEvent.service     == service,
                    MetricEvent.metric_name == name,
                    MetricEvent.timestamp   >= start,
                    MetricEvent.timestamp   <= end,
                )
            ).all()
            if rows:
                metrics[name] = sum(r.value for r in rows) / len(rows)
        return metrics

    def create_incident_if_anomalies(self, service: str) -> Incident:
        anomalies, trigger_metrics, incident_start = self.detect_anomalies(service)
        if not anomalies:
            return None

        severity = "HIGH" if len(anomalies) >= 2 else "MEDIUM"

        # Don't create duplicate
        existing = self.db.query(Incident).filter(
            and_(
                Incident.service    == service,
                Incident.status     == "ACTIVE",
                Incident.start_time >= incident_start - timedelta(minutes=5),
            )
        ).first()
        if existing:
            return existing

        incident = Incident(
            incident_id     = f"INC-{uuid4().hex[:12].upper()}",
            service         = service,
            start_time      = incident_start,
            severity        = severity,
            status          = "ACTIVE",
            trigger_metrics = trigger_metrics,
            description     = f"Anomalies: {', '.join(anomalies)}",
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident
