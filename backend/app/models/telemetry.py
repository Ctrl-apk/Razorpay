from sqlalchemy import Column, String, DateTime, Float, JSON
from sqlalchemy.types import TypeDecorator, String as SAString
from datetime import datetime
import uuid

from ..database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID (UUID on Postgres, VARCHAR on SQLite)."""
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


class MetricEvent(Base):
    __tablename__ = "metric_events"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp   = Column(DateTime, nullable=False, index=True)
    service     = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    value       = Column(Float, nullable=False)
    unit        = Column(String, nullable=True)
    labels      = Column(JSON, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class LogEvent(Base):
    __tablename__ = "log_events"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp  = Column(DateTime, nullable=False, index=True)
    service    = Column(String, nullable=False, index=True)
    level      = Column(String, nullable=False)
    message    = Column(String, nullable=False)
    extra_data = Column(JSON, nullable=True)   # renamed: 'metadata' is reserved by SQLAlchemy
    created_at = Column(DateTime, default=datetime.utcnow)


class TraceEvent(Base):
    __tablename__ = "trace_events"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp   = Column(DateTime, nullable=False, index=True)
    service     = Column(String, nullable=False, index=True)
    trace_id    = Column(String, nullable=False)
    span_id     = Column(String, nullable=False)
    operation   = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=False)
    status      = Column(String, nullable=False)
    extra_data  = Column(JSON, nullable=True)   # renamed: 'metadata' is reserved
    created_at  = Column(DateTime, default=datetime.utcnow)


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp   = Column(DateTime, nullable=False, index=True)
    service     = Column(String, nullable=False, index=True)
    version     = Column(String, nullable=False)
    commit_sha  = Column(String, nullable=True)
    author      = Column(String, nullable=True)
    environment = Column(String, nullable=False, default="production")
    status      = Column(String, nullable=False, default="success")
    created_at  = Column(DateTime, default=datetime.utcnow)
