from pydantic import BaseModel, Field


class ResultSheetIds(BaseModel):
    sheet_ids: list[int] = Field(min_length=1)
