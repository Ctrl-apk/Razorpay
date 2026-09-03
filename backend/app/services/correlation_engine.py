from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.telemetry import MetricEvent, LogEvent, DeploymentEvent
from typing import List, Dict, Any


class CorrelationEngine:
    """Temporal correlation engine for incidents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.correlation_window_minutes = 15
    
    def correlate_events(self, incident_start: datetime, service: str) -> Dict[str, Any]:
        """Correlate all events around an incident."""
        window_start = incident_start - timedelta(minutes=self.correlation_window_minutes)
        window_end = incident_start + timedelta(minutes=self.correlation_window_minutes)
        
        correlations = {
            "deployments": self._correlate_deployments(service, window_start, window_end),
            "metric_anomalies": self._correlate_metrics(service, window_start, window_end),
            "log_errors": self._correlate_logs(service, window_start, window_end),
            "timeline": self._build_timeline(service, window_start, window_end, incident_start),
        }
        
        return correlations
    
    def _correlate_deployments(self, service: str, start: datetime, end: datetime) -> List[Dict]:
        """Find deployments within the time window."""
        incident_start = start + timedelta(minutes=self.correlation_window_minutes)
        deployments = self.db.query(DeploymentEvent).filter(
            and_(
                DeploymentEvent.service == service,
                DeploymentEvent.timestamp >= start,
                DeploymentEvent.timestamp <= end,
            )
        ).order_by(DeploymentEvent.timestamp).all()

        result = []
        for dep in deployments:
            # minutes before incident (positive = before, negative = after)
            minutes_before = (incident_start - dep.timestamp).total_seconds() / 60
            result.append({
                "version": dep.version,
                "timestamp": dep.timestamp.isoformat(),
                "commit_sha": dep.commit_sha,
                "author": dep.author,
                "minutes_before_incident": minutes_before,
                "strength": self._calc_deployment_correlation_strength(minutes_before),
            })

        return result
    
    def _correlate_metrics(self, service: str, start: datetime, end: datetime) -> List[Dict]:
        """Find metric anomalies within the window."""
        metrics = self.db.query(MetricEvent).filter(
            and_(
                MetricEvent.service == service,
                MetricEvent.metric_name.in_([
                    "error_rate", "latency_p95", "db_connections",
                    "cpu_usage", "requests_per_second", "dependency_latency",
                ]),
                MetricEvent.timestamp >= start,
                MetricEvent.timestamp <= end,
            )
        ).order_by(MetricEvent.timestamp).all()

        # Group by metric name and find anomalies
        metric_groups: dict = {}
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric)

        result = []
        for metric_name, values in metric_groups.items():
            if len(values) >= 1:
                avg_value = sum(v.value for v in values) / len(values)
                result.append({
                    "metric": metric_name,
                    "average": avg_value,
                    "samples": len(values),
                    "first_observation": values[0].timestamp.isoformat(),
                })

        return result
    
    def _correlate_logs(self, service: str, start: datetime, end: datetime) -> List[Dict]:
        """Find error logs within the window."""
        errors = self.db.query(LogEvent).filter(
            and_(
                LogEvent.service == service,
                LogEvent.level.in_(["ERROR", "WARN"]),
                LogEvent.timestamp >= start,
                LogEvent.timestamp <= end,
            )
        ).order_by(LogEvent.timestamp).all()
        
        result = []
        for error in errors:
            result.append({
                "timestamp": error.timestamp.isoformat(),
                "level": error.level,
                "message": error.message,
                "extra_data": error.extra_data,
            })
        
        return result
    
    def _build_timeline(self, service: str, start: datetime, end: datetime, incident_start: datetime) -> List[Dict]:
        """Build a unified timeline of all events."""
        timeline = []
        
        # Add deployments
        deployments = self.db.query(DeploymentEvent).filter(
            and_(
                DeploymentEvent.service == service,
                DeploymentEvent.timestamp >= start,
                DeploymentEvent.timestamp <= end,
            )
        ).all()
        
        for dep in deployments:
            timeline.append({
                "timestamp": dep.timestamp.isoformat(),
                "type": "deployment",
                "version": dep.version,
                "commit_sha": dep.commit_sha,
            })
        
        # Add metrics
        metrics = self.db.query(MetricEvent).filter(
            and_(
                MetricEvent.service == service,
                MetricEvent.metric_name.in_([
                    "error_rate", "latency_p95", "db_connections",
                    "cpu_usage", "requests_per_second", "dependency_latency",
                ]),
                MetricEvent.timestamp >= start,
                MetricEvent.timestamp <= end,
            )
        ).all()
        
        for metric in metrics:
            timeline.append({
                "timestamp": metric.timestamp.isoformat(),
                "type": "metric",
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
            })
        
        # Add errors
        errors = self.db.query(LogEvent).filter(
            and_(
                LogEvent.service == service,
                LogEvent.level.in_(["ERROR", "WARN"]),
                LogEvent.timestamp >= start,
                LogEvent.timestamp <= end,
            )
        ).all()
        
        for error in errors:
            timeline.append({
                "timestamp": error.timestamp.isoformat(),
                "type": "log",
                "level": error.level,
                "message": error.message,
            })
        
        # Add incident marker
        timeline.append({
            "timestamp": incident_start.isoformat(),
            "type": "incident_start",
        })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
    
    def _calc_deployment_correlation_strength(self, minutes_before: float) -> float:
        """Calculate correlation strength for deployment timing."""
        if minutes_before < 0:
            return 0.0
        if minutes_before < 5:
            return 1.0
        if minutes_before < 10:
            return 0.8
        if minutes_before < 15:
            return 0.5
        return 0.0
