from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List
from uuid import uuid4

from ..database import get_db
from ..models.incident import Incident, Investigation
from ..schemas.incident import IncidentCreateSchema, IncidentResponseSchema, InvestigationResponseSchema

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.post("", response_model=IncidentResponseSchema)
async def create_incident(incident: IncidentCreateSchema, db: Session = Depends(get_db)):
    db_incident = Incident(
        incident_id     = f"INC-{uuid4().hex[:12].upper()}",
        service         = incident.service,
        start_time      = datetime.utcnow(),
        severity        = incident.severity,
        trigger_metrics = incident.trigger_metrics,
        description     = incident.description,
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return IncidentResponseSchema.model_validate(db_incident)


@router.get("", response_model=List[IncidentResponseSchema])
async def list_incidents(
    service: str = None,
    status:  str = None,
    limit:   int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Incident).order_by(desc(Incident.start_time))
    if service:
        q = q.filter(Incident.service == service)
    if status:
        q = q.filter(Incident.status == status)
    return [IncidentResponseSchema.model_validate(i) for i in q.limit(limit).all()]


@router.get("/{incident_id}", response_model=IncidentResponseSchema)
async def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponseSchema.model_validate(inc)


@router.patch("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status   = "RESOLVED"
    inc.end_time = datetime.utcnow()
    inc.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "resolved", "incident_id": incident_id}


@router.get("/{incident_id}/investigation")
async def get_investigation(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inv = db.query(Investigation).filter(Investigation.incident_id == inc.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="No investigation yet")
    return InvestigationResponseSchema.model_validate(inv)
