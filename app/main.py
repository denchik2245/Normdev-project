from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.audit import router as audit_router
from app.api.web import router as web_router
from app.config import settings
from app.core.database import Base, engine
from app.models import Audit, AuditIssue, AuditMetric, AuditReport  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(audit_router)
app.include_router(web_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Site Audit Service is running"
    }


@app.get("/health", tags=["Health"])
def healthcheck():
    return {
        "status": "ok"
    }