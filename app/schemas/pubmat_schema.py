from datetime import datetime

from pydantic import BaseModel


class PubMatAttach(BaseModel):
    asset_url: str
    asset_type: str
    description: str | None = None
    tags: list[str] = []


class PubMatResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    article_id: int
    asset_url: str
    asset_type: str
    uploaded_by: int
    uploaded_at: datetime
