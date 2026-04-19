from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models.audit import Audit
from app.models.issue import AuditIssue
from app.models.metric import AuditMetric
from app.models.report import AuditReport


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_audit(self, url: str, status: str = "pending") -> Audit:
        audit = Audit(url=url, status=status)
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def update_audit_status(
        self,
        audit: Audit,
        status: str,
        total_score: float | None = None,
        finished: bool = False
    ) -> Audit:
        audit.status = status

        if total_score is not None:
            audit.total_score = total_score

        if finished:
            audit.finished_at = datetime.utcnow()

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def add_metric(
        self,
        audit_id: int,
        metric_name: str,
        metric_value: float,
        unit: str | None = None
    ) -> AuditMetric:
        metric = AuditMetric(
            audit_id=audit_id,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def add_issue(
        self,
        audit_id: int,
        category: str,
        severity: str,
        title: str,
        description: str,
        recommendation: str | None = None
    ) -> AuditIssue:
        issue = AuditIssue(
            audit_id=audit_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def add_report(self, audit_id: int, file_path: str) -> AuditReport:
        report = AuditReport(
            audit_id=audit_id,
            file_path=file_path
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_latest_report_by_audit_id(self, audit_id: int) -> AuditReport | None:
        return (
            self.db.query(AuditReport)
            .filter(AuditReport.audit_id == audit_id)
            .order_by(AuditReport.generated_at.desc())
            .first()
        )

    def get_audits(self) -> list[Audit]:
        return (
            self.db.query(Audit)
            .order_by(Audit.created_at.desc())
            .all()
        )

    def get_audit_by_id(self, audit_id: int) -> Audit | None:
        return (
            self.db.query(Audit)
            .options(
                selectinload(Audit.issues),
                selectinload(Audit.metrics),
                selectinload(Audit.reports),
            )
            .filter(Audit.id == audit_id)
            .first()
        )