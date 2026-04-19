from pydantic import BaseModel


class AuditMetricBase(BaseModel):
    metric_name: str
    metric_value: float
    unit: str | None = None


class AuditMetricResponse(AuditMetricBase):
    id: int
    audit_id: int

    model_config = {
        "from_attributes": True
    }