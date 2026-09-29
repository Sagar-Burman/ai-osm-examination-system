from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModerationDecision(str, Enum):
    APPROVE = "APPROVE"
    OVERRIDE = "OVERRIDE"
    REQUEST_REVIEW = "REQUEST_REVIEW"
    NOTE = "NOTE"


class Moderation(Base):
    __tablename__ = "moderation"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    flag_id: Mapped[int] = mapped_column(
        ForeignKey("flags.id"),
        nullable=False,
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False,
    )

    moderator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    decision: Mapped[ModerationDecision] = mapped_column(
        String(30),
        nullable=False,
    )

    old_total: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    new_total: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
