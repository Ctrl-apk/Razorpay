from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class MetricEventSchema(BaseModel):
    timestamp:   datetime
    service:     str
    metric_name: str
    value:       float
    unit:        Optional[str] = None
    labels:      Optional[Dict[str, Any]] = None


class LogEventSchema(BaseModel):
    timestamp:  datetime
    service:    str
    level:      str
    message:    str
    extra_data: Optional[Dict[str, Any]] = None   # was 'metadata'


class TraceEventSchema(BaseModel):
    timestamp:   datetime
    service:     str
    trace_id:    str
    span_id:     str
    operation:   str
    duration_ms: float
    status:      str
    extra_data:  Optional[Dict[str, Any]] = None  # was 'metadata'


class DeploymentEventSchema(BaseModel):
    timestamp:   datetime
    service:     str
    version:     str
    commit_sha:  Optional[str] = None
    author:      Optional[str] = None
    environment: str = "production"
    status:      str = "success"
