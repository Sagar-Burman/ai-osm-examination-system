from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnnotationCreate(BaseModel):
    page_no: int = Field(ge=1)
    type: str
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    w: Optional[float] = Field(default=None, ge=0, le=1)
    h: Optional[float] = Field(default=None, ge=0, le=1)
    question_id: Optional[int] = None
    text: Optional[str] = None


class AnnotationResponse(BaseModel):
    id: int
    sheet_id: int
    page_no: int
    question_id: Optional[int] = None
    type: str
    x: float
    y: float
    w: Optional[float] = None
    h: Optional[float] = None
    text: Optional[str] = None
    examiner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)