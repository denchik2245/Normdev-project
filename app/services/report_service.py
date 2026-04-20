from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.config import settings
from app.utils.helpers import (
    calculate_category_score,
    count_problematic_metrics,
    format_metric_value,
    get_metric_display_name,
    get_metric_severity,
    group_metrics_by_category,
)


class ReportService:
    def __init__(self):
        self.templates_dir = Path("app/templates")
        self.reports_dir = Path(settings.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate_audit_report(self, audit) -> str:
        template = self.env.get_template("report_template.html")
        grouped_issues = {
            "seo": [issue for issue in audit.issues if issue.category == "seo"],
            "technical": [issue for issue in audit.issues if issue.category == "technical"],
            "performance": [issue for issue in audit.issues if issue.category == "performance"],
        }
        grouped_metrics = group_metrics_by_category(audit.metrics)
        category_scores = {
            "seo": calculate_category_score(grouped_issues["seo"]),
            "technical": calculate_category_score(grouped_issues["technical"]),
            "performance": calculate_category_score(grouped_issues["performance"]),
        }
        problematic_metrics_count = {
            "seo": count_problematic_metrics(grouped_metrics["seo"]),
            "technical": count_problematic_metrics(grouped_metrics["technical"]),
            "performance": count_problematic_metrics(grouped_metrics["performance"]),
        }

        html_content = template.render(
            audit=audit,
            title=f"Отчет по аудиту сайта #{audit.id}",
            grouped_metrics=grouped_metrics,
            grouped_issues=grouped_issues,
            category_scores=category_scores,
            problematic_metrics_count=problematic_metrics_count,
            get_metric_display_name=get_metric_display_name,
            get_metric_severity=get_metric_severity,
            format_metric_value=format_metric_value,
        )

        output_path = self.reports_dir / f"audit_report_{audit.id}.pdf"

        HTML(string=html_content, base_url=str(Path.cwd())).write_pdf(output_path)

        return str(output_path)
