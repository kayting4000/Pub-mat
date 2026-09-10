from pydantic import BaseModel


class ReviewRequest(BaseModel):
    action: str  # "approve" | "reject"
    comment: str | None = None
