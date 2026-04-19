from app.repositories.audit_repository import AuditRepository
from app.services.page_loader import PageLoader, PageLoaderError
from app.services.performance_analyzer import PerformanceAnalyzer
from app.services.report_service import ReportService
from app.services.score_calculator import ScoreCalculator
from app.services.seo_analyzer import SEOAnalyzer
from app.services.technical_analyzer import TechnicalAnalyzer


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository
        self.page_loader = PageLoader()
        self.seo_analyzer = SEOAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.score_calculator = ScoreCalculator()
        self.report_service = ReportService()

    def run_initial_audit(self, url: str):
        audit = self.repository.create_audit(url=url, status="running")

        try:
            page_result = self.page_loader.load(url)

            self.repository.add_metric(
                audit_id=audit.id,
                metric_name="status_code",
                metric_value=float(page_result.status_code),
                unit=None,
            )
            self.repository.add_metric(
                audit_id=audit.id,
                metric_name="response_time",
                metric_value=page_result.response_time_ms,
                unit="ms",
            )
            self.repository.add_metric(
                audit_id=audit.id,
                metric_name="html_size",
                metric_value=float(len(page_result.html.encode("utf-8"))),
                unit="bytes",
            )

            seo_result = self.seo_analyzer.analyze(page_result.html)
            technical_result = self.technical_analyzer.analyze(
                original_url=url,
                final_url=page_result.final_url,
                html=page_result.html,
                status_code=page_result.status_code,
                headers=page_result.headers,
                is_https=page_result.is_https,
            )
            performance_result = self.performance_analyzer.analyze(
                html=page_result.html,
                response_time_ms=page_result.response_time_ms,
            )

            for metric_name, metric_value, unit in seo_result.metrics:
                self.repository.add_metric(
                    audit_id=audit.id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    unit=unit,
                )

            for metric_name, metric_value, unit in technical_result.metrics:
                self.repository.add_metric(
                    audit_id=audit.id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    unit=unit,
                )

            for metric_name, metric_value, unit in performance_result.metrics:
                self.repository.add_metric(
                    audit_id=audit.id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    unit=unit,
                )

            for issue in seo_result.issues:
                self.repository.add_issue(
                    audit_id=audit.id,
                    category="seo",
                    severity=issue.severity,
                    title=issue.title,
                    description=issue.description,
                    recommendation=issue.recommendation,
                )

            for issue in technical_result.issues:
                self.repository.add_issue(
                    audit_id=audit.id,
                    category="technical",
                    severity=issue.severity,
                    title=issue.title,
                    description=issue.description,
                    recommendation=issue.recommendation,
                )

            for issue in performance_result.issues:
                self.repository.add_issue(
                    audit_id=audit.id,
                    category="performance",
                    severity=issue.severity,
                    title=issue.title,
                    description=issue.description,
                    recommendation=issue.recommendation,
                )

            total_score = self.score_calculator.calculate(
                status_code=page_result.status_code,
                is_https=page_result.is_https,
                seo_issues=seo_result.issues,
                technical_issues=technical_result.issues,
                performance_issues=performance_result.issues,
            )

            self.repository.update_audit_status(
                audit=audit,
                status="completed",
                total_score=total_score,
                finished=True
            )

            full_audit = self.repository.get_audit_by_id(audit.id)
            report_path = self.report_service.generate_audit_report(full_audit)
            self.repository.add_report(
                audit_id=audit.id,
                file_path=report_path
            )

            return {
                "audit": self.repository.get_audit_by_id(audit.id),
                "error": None,
            }

        except PageLoaderError as exc:
            self.repository.update_audit_status(
                audit=audit,
                status="failed",
                total_score=0.0,
                finished=True
            )

            return {
                "audit": self.repository.get_audit_by_id(audit.id),
                "error": str(exc),
            }