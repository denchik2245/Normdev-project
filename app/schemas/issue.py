from pydantic import BaseModel


class AuditIssueBase(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    recommendation: str | None = None


class AuditIssueResponse(AuditIssueBase):
    id: int
    audit_id: int

    model_config = {
        "from_attributes": True
    }