from pydantic import BaseModel, Field, field_validator


class RubricBreakdownItem(BaseModel):
    item: str
    max: float
    awarded: float
    covered: bool

    @field_validator("awarded")
    @classmethod
    def awarded_non_negative(cls, value):
        if value < 0:
            raise ValueError("awarded cannot be negative")
        return value


class AISuggestionResponse(BaseModel):
    suggested_marks: float
    max_marks: float
    rubric_breakdown: list[RubricBreakdownItem]
    strengths: list[str]
    missing_concepts: list[str]
    summary: str
    confidence: str
    ocr_concern: bool