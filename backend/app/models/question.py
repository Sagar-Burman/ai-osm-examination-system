from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False
    )

    question_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    max_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    rubric: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    model_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    is_optional: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )