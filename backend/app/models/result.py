from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False)
    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"), unique=True, nullable=False
    )
    roll_no: Mapped[str] = mapped_column(String(100), nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    question_marks: Mapped[dict] = mapped_column(JSON, nullable=False)
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    released_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
