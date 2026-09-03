from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..models.incident import Incident, Investigation
from ..services.investigation_service import InvestigationService
from ..schemas.incident import InvestigationResponseSchema

router = APIRouter(prefix="/api/v1/incidents", tags=["investigations"])


@router.post("/{incident_id}/investigate")
async def trigger_investigation(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Trigger an AI investigation for an incident."""
    service = InvestigationService(db)
    try:
        investigation = await service.investigate(incident_id)
        return {
            "status": "completed",
            "incident_id": incident_id,
            "root_cause": investigation.root_cause,
            "confidence_score": investigation.confidence_score,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@router.get("/{incident_id}/timeline")
async def get_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Get the event timeline for an incident."""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    investigation = (
        db.query(Investigation)
        .filter(Investigation.incident_id == incident.id)
        .first()
    )

    if investigation and investigation.evidence_package:
        timeline = investigation.evidence_package.get("timeline", [])
        return {"incident_id": incident_id, "timeline": timeline}

    return {"incident_id": incident_id, "timeline": []}


@router.get("/{incident_id}/evidence")
async def get_evidence(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Get the full evidence package for an incident."""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    investigation = (
        db.query(Investigation)
        .filter(Investigation.incident_id == incident.id)
        .first()
    )

    if not investigation:
        raise HTTPException(status_code=404, detail="No investigation found")

    return {
        "incident_id": incident_id,
        "evidence_package": investigation.evidence_package,
        "hypotheses": investigation.hypotheses,
        "recommended_actions": investigation.recommended_actions,
    }
