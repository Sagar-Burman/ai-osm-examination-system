from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False
    )

    suggested_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    response: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    prompt_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    validation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )