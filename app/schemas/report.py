from datetime import datetime

from pydantic import BaseModel


class AuditReportResponse(BaseModel):
    id: int
    audit_id: int
    file_path: str
    generated_at: datetime

    model_config = {
        "from_attributes": True
    }