from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

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
        nullable=False
    )