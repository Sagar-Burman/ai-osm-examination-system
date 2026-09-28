from datetime import date

from pydantic import BaseModel, Field


class ExamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    subject: str = Field(min_length=1, max_length=100)
    exam_date: date
    total_marks: int = Field(gt=0)
    expected_pages: int | None = Field(default=None, gt=0)
    mark_step: float = Field(default=0.5, gt=0)


class ExamResponse(BaseModel):
    id: int
    name: str
    subject: str
    exam_date: date
    total_marks: int
    expected_pages: int | None
    mark_step: float
    is_locked: bool
    created_by: int

    model_config = {
        "from_attributes": True
    }