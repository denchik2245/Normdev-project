from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditCreateRequest, AuditListResponse, AuditResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.post(
    "",
    response_model=AuditResponse,
    status_code=status.HTTP_201_CREATED
)
def create_audit(
    payload: AuditCreateRequest,
    db: Session = Depends(get_db)
):
    repository = AuditRepository(db)
    service = AuditService(repository)
    result = service.run_initial_audit(url=str(payload.url))

    if result["audit"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit"
        )

    return result["audit"]


@router.get(
    "",
    response_model=list[AuditListResponse]
)
def get_audits(db: Session = Depends(get_db)):
    repository = AuditRepository(db)
    audits = repository.get_audits()
    return audits


@router.get(
    "/{audit_id}",
    response_model=AuditResponse
)
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    repository = AuditRepository(db)
    audit = repository.get_audit_by_id(audit_id)

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found"
        )

    return audit


@router.get("/{audit_id}/report")
def download_audit_report(audit_id: int, db: Session = Depends(get_db)):
    repository = AuditRepository(db)
    report = repository.get_latest_report_by_audit_id(audit_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    report_path = Path(report.file_path)

    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file does not exist"
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_path.name
    )