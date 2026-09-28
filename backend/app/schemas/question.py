from pydantic import BaseModel, Field, model_validator


class RubricItem(BaseModel):
    item: str = Field(min_length=1)
    marks: float = Field(gt=0)


class QuestionCreate(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    text: str = Field(min_length=1)
    max_marks: float = Field(gt=0)
    rubric: list[RubricItem] = Field(min_length=1)
    model_answer: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rubric_total(self):
        rubric_total = sum(item.marks for item in self.rubric)

        if abs(rubric_total - self.max_marks) > 0.001:
            raise ValueError("Rubric marks must sum to max_marks")

        return self


class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    number: str
    text: str
    max_marks: float
    rubric: list[RubricItem]
    model_answer: str

    model_config = {
        "from_attributes": True
    }