from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    subject: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    exam_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    total_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    expected_pages: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    mark_step: Mapped[float] = mapped_column(
        default=0.5,
        nullable=False
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )