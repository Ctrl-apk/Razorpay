import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from ..database import get_db
from ..models.telemetry import MetricEvent, LogEvent, DeploymentEvent
from ..models.incident import Incident

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

SCENARIOS_DIR = Path(__file__).parent.parent.parent.parent / "scenarios"


def _load_scenario(name: str) -> dict:
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    with open(path) as f:
        return json.load(f)


@router.get("")
def list_scenarios():
    if not SCENARIOS_DIR.exists():
        return {"scenarios": []}
    return {"scenarios": [p.stem for p in sorted(SCENARIOS_DIR.glob("*.json"))]}


@router.post("/{scenario_name}/run")
async def run_scenario(scenario_name: str, db: Session = Depends(get_db)):
    scenario = _load_scenario(scenario_name)
    service  = scenario["service"]

    # Clear previous telemetry for this service so scenarios stay isolated
    db.query(MetricEvent).filter(MetricEvent.service == service).delete()
    db.query(LogEvent).filter(LogEvent.service == service).delete()
    db.query(DeploymentEvent).filter(DeploymentEvent.service == service).delete()
    db.flush()

    for m in scenario.get("metrics", []):
        db.add(MetricEvent(
            timestamp   = datetime.fromisoformat(m["timestamp"]),
            service     = service,
            metric_name = m["metric_name"],
            value       = m["value"],
            unit        = m.get("unit"),
            labels      = m.get("labels"),
        ))

    for l in scenario.get("logs", []):
        db.add(LogEvent(
            timestamp  = datetime.fromisoformat(l["timestamp"]),
            service    = service,
            level      = l["level"],
            message    = l["message"],
            extra_data = l.get("extra_data"),
        ))

    for d in scenario.get("deployments", []):
        db.add(DeploymentEvent(
            timestamp   = datetime.fromisoformat(d["timestamp"]),
            service     = service,
            version     = d["version"],
            commit_sha  = d.get("commit_sha"),
            author      = d.get("author"),
            environment = d.get("environment", "production"),
            status      = d.get("status", "success"),
        ))

    db.flush()

    incident_id = f"INC-{uuid4().hex[:12].upper()}"
    incident = Incident(
        incident_id     = incident_id,
        service         = service,
        start_time      = datetime.fromisoformat(scenario["incident_start"]),
        severity        = scenario.get("severity", "HIGH"),
        status          = "ACTIVE",
        trigger_metrics = scenario.get("trigger_metrics"),
        description     = scenario.get("description", f"Demo: {scenario_name}"),
    )
    db.add(incident)
    db.commit()

    return {
        "status":      "seeded",
        "scenario":    scenario_name,
        "incident_id": incident_id,
        "service":     service,
        "message":     f"Scenario loaded. POST /api/v1/incidents/{incident_id}/investigate to run AI analysis.",
    }
