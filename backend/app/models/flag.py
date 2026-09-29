from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False,
    )

    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("questions.id"),
        nullable=True,
    )

    type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metric_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    related_sheet_id: Mapped[int | None] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )

    created_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SYSTEM",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
