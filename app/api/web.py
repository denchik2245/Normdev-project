from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.utils.helpers import (
    format_datetime,
    format_metric_value,
    get_metric_display_name,
    get_score_class,
    get_score_label,
    get_status_label,
)
from app.utils.validators import normalize_url

router = APIRouter(tags=["Web"])

templates = Jinja2Templates(directory="app/templates")


def group_issues_by_category(issues):
    grouped = {
        "seo": [],
        "technical": [],
        "performance": [],
    }

    for issue in issues:
        if issue.category in grouped:
            grouped[issue.category].append(issue)
        else:
            grouped.setdefault(issue.category, []).append(issue)

    return grouped


@router.get("/web", response_class=HTMLResponse)
def web_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Аудит сайтов",
            "error": None,
            "url_value": "",
        }
    )


@router.post("/web/audits", response_class=HTMLResponse)
def web_create_audit(
    request: Request,
    url: str = Form(...),
    db: Session = Depends(get_db)
):
    normalized_url = normalize_url(url)

    if not normalized_url:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "Аудит сайтов",
                "error": "Введите корректный URL сайта.",
                "url_value": url,
            },
            status_code=400
        )

    repository = AuditRepository(db)
    service = AuditService(repository)
    result = service.run_initial_audit(url=normalized_url)

    if result["error"]:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "Аудит сайтов",
                "error": result["error"],
                "url_value": normalized_url,
            },
            status_code=400
        )

    audit = result["audit"]

    return RedirectResponse(
        url=f"/web/audits/{audit.id}",
        status_code=303
    )


@router.get("/web/audits/{audit_id}", response_class=HTMLResponse)
def web_audit_detail(
    audit_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    repository = AuditRepository(db)
    audit = repository.get_audit_by_id(audit_id)

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аудит не найден"
        )

    grouped_issues = group_issues_by_category(audit.issues)

    return templates.TemplateResponse(
        request=request,
        name="audit_detail.html",
        context={
            "title": f"Аудит #{audit_id}",
            "audit": audit,
            "grouped_issues": grouped_issues,
            "seo_issues_count": len(grouped_issues.get("seo", [])),
            "technical_issues_count": len(grouped_issues.get("technical", [])),
            "performance_issues_count": len(grouped_issues.get("performance", [])),
            "get_metric_display_name": get_metric_display_name,
            "format_metric_value": format_metric_value,
            "get_score_label": get_score_label,
            "get_score_class": get_score_class,
            "get_status_label": get_status_label,
            "format_datetime": format_datetime,
        }
    )


@router.get("/web/history", response_class=HTMLResponse)
def web_history(
    request: Request,
    db: Session = Depends(get_db)
):
    repository = AuditRepository(db)
    audits = repository.get_audits()

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "title": "История проверок",
            "audits": audits,
            "get_score_label": get_score_label,
            "get_score_class": get_score_class,
            "get_status_label": get_status_label,
            "format_datetime": format_datetime,
        }
    )