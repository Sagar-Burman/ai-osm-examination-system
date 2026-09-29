from pydantic import BaseModel, Field


class OverrideMark(BaseModel):
    question_id: int
    marks: float = Field(ge=0)


class ModerationDecisionRequest(BaseModel):
    flag_id: int
    decision: str
    new_marks: list[OverrideMark] = Field(default_factory=list)
    note: str | None = None
