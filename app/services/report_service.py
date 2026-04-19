from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.config import settings


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

        html_content = template.render(
            audit=audit,
            title=f"Отчет по аудиту сайта #{audit.id}"
        )

        output_path = self.reports_dir / f"audit_report_{audit.id}.pdf"

        HTML(string=html_content, base_url=str(Path.cwd())).write_pdf(output_path)

        return str(output_path)