from datetime import datetime

from pydantic import BaseModel


class PublishRequest(BaseModel):
    draft_id: str
    title: str
    category_id: int | None = None


class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    draft_id: str
    author_id: int
    category_id: int | None = None
    published_at: datetime
