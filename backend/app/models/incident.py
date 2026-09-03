from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import TypeDecorator, String as SAString
from datetime import datetime
import uuid


from ..database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type (UUID on Postgres, VARCHAR on SQLite)."""
    impl = SAString
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


class Incident(Base):
    __tablename__ = "incidents"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    incident_id  = Column(String, unique=True, nullable=False, index=True)
    service      = Column(String, nullable=False, index=True)
    start_time   = Column(DateTime, nullable=False, index=True)
    end_time     = Column(DateTime, nullable=True)
    severity     = Column(String, nullable=False, default="MEDIUM")
    status       = Column(String, nullable=False, default="ACTIVE")
    trigger_metrics = Column(JSON, nullable=True)
    description  = Column(String, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Investigation(Base):
    __tablename__ = "investigations"

    id                 = Column(GUID, primary_key=True, default=uuid.uuid4)
    incident_id        = Column(GUID, ForeignKey("incidents.id"), nullable=False, index=True)
    root_cause         = Column(String, nullable=True)
    confidence_score   = Column(Float, nullable=True)
    causal_narrative   = Column(String, nullable=True)
    evidence_package   = Column(JSON, nullable=True)
    hypotheses         = Column(JSON, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    created_at         = Column(DateTime, default=datetime.utcnow)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
