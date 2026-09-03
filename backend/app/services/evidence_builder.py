from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any
from .correlation_engine import CorrelationEngine


class EvidenceBuilder:
    """Builds evidence packages for AI investigation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.correlation_engine = CorrelationEngine(db)
    
    def build_evidence_package(self, incident_id: str, service: str, incident_start: datetime) -> Dict[str, Any]:
        """Build a compact evidence package for investigation."""
        
        correlations = self.correlation_engine.correlate_events(incident_start, service)
        
        evidence_package = {
            "incident": {
                "incident_id": incident_id,
                "service": service,
                "started_at": incident_start.isoformat(),
            },
            "deployments": correlations.get("deployments", []),
            "metric_anomalies": correlations.get("metric_anomalies", []),
            "error_logs": correlations.get("log_errors", []),
            "timeline": correlations.get("timeline", []),
            "meta": {
                "evidence_built_at": datetime.utcnow().isoformat(),
                "correlation_window_minutes": 15,
            }
        }
        
        return evidence_package
