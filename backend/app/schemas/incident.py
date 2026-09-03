from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class IncidentCreateSchema(BaseModel):
    service: str
    severity: str = "MEDIUM"   # LOW | MEDIUM | HIGH | CRITICAL
    trigger_metrics: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class IncidentResponseSchema(BaseModel):
    id: UUID
    incident_id: str
    service: str
    start_time: datetime
    end_time: Optional[datetime] = None
    severity: str
    status: str
    trigger_metrics: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HypothesisSchema(BaseModel):
    hypothesis_name: str
    status: str
    reasoning: str
    evidence_for: List[str] = []
    evidence_against: List[str] = []


class InvestigationResponseSchema(BaseModel):
    id: UUID
    incident_id: UUID
    root_cause: Optional[str] = None
    confidence_score: Optional[float] = None
    causal_narrative: Optional[str] = None
    evidence_package: Optional[Dict[str, Any]] = None
    hypotheses: Optional[List[Dict[str, Any]]] = None
    recommended_actions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
