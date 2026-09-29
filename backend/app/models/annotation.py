from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sheet_id: Mapped[int] = mapped_column(ForeignKey("sheets.id"), nullable=False, index=True)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("questions.id"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    w: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examiner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
