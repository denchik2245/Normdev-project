from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.issue import AuditIssueResponse
from app.schemas.metric import AuditMetricResponse
from app.schemas.report import AuditReportResponse


class AuditCreateRequest(BaseModel):
    url: HttpUrl


class AuditListResponse(BaseModel):
    id: int
    url: str
    status: str
    total_score: float | None = None
    created_at: datetime
    finished_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class AuditResponse(BaseModel):
    id: int
    url: str
    status: str
    total_score: float | None = None
    created_at: datetime
    finished_at: datetime | None = None
    issues: list[AuditIssueResponse] = Field(default_factory=list)
    metrics: list[AuditMetricResponse] = Field(default_factory=list)
    reports: list[AuditReportResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }