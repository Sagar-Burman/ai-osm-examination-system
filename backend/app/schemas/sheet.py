from pydantic import BaseModel


class SheetUploadResponse(BaseModel):
    sheet_id: int
    qc_status: str
    status: str
    anonymous_code: str | None