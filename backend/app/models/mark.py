from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Mark(Base):
    __tablename__ = "marks"

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

    final_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    eval_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    ai_suggestion_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_suggestions.id"),
        nullable=True
    )

    ai_action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NONE"
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    examiner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "sheet_id",
            "question_id",
            name="uq_marks_sheet_question"
        ),
    )