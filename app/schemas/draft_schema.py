from datetime import datetime

from pydantic import BaseModel


class DraftCreate(BaseModel):
    title: str
    content: str
    category_id: int | None = None


class DraftUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None


class DraftResponse(BaseModel):
    id: str | None = None
    title: str
    content: str
    author_id: int
    category_id: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime
