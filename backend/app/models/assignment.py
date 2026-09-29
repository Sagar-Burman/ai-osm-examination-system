from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False,
        unique=True
    )

    examiner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ASSIGNED"
    )

    first_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )