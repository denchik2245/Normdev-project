from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    issues = relationship(
        "AuditIssue",
        back_populates="audit",
        cascade="all, delete-orphan"
    )
    metrics = relationship(
        "AuditMetric",
        back_populates="audit",
        cascade="all, delete-orphan"
    )
    reports = relationship(
        "AuditReport",
        back_populates="audit",
        cascade="all, delete-orphan"
    )