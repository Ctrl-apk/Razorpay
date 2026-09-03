from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.telemetry import MetricEvent, LogEvent, TraceEvent, DeploymentEvent
from ..schemas.telemetry import (
    MetricEventSchema,
    LogEventSchema,
    TraceEventSchema,
    DeploymentEventSchema,
)

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.post("/metrics")
async def ingest_metrics(event: MetricEventSchema, db: Session = Depends(get_db)):
    db_event = MetricEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"id": str(db_event.id), "created_at": db_event.created_at}


@router.post("/logs")
async def ingest_logs(event: LogEventSchema, db: Session = Depends(get_db)):
    db_event = LogEvent(
        timestamp  = event.timestamp,
        service    = event.service,
        level      = event.level,
        message    = event.message,
        extra_data = event.extra_data,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"id": str(db_event.id), "created_at": db_event.created_at}


@router.post("/traces")
async def ingest_traces(event: TraceEventSchema, db: Session = Depends(get_db)):
    db_event = TraceEvent(
        timestamp   = event.timestamp,
        service     = event.service,
        trace_id    = event.trace_id,
        span_id     = event.span_id,
        operation   = event.operation,
        duration_ms = event.duration_ms,
        status      = event.status,
        extra_data  = event.extra_data,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"id": str(db_event.id), "created_at": db_event.created_at}


@router.post("/deployments")
async def ingest_deployments(event: DeploymentEventSchema, db: Session = Depends(get_db)):
    db_event = DeploymentEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"id": str(db_event.id), "created_at": db_event.created_at}
