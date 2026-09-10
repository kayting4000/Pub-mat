from datetime import datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if isinstance(v, ObjectId):
            return str(v)
        if ObjectId.is_valid(v):
            return str(v)
        raise ValueError("Invalid ObjectId")


class Revision(BaseModel):
    content: str
    revised_at: datetime = Field(default_factory=datetime.utcnow)
    revised_by: int  # user_id


class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    author_id: int
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Draft(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    title: str
    content: str
    author_id: int
    category_id: int | None = None
    status: str = "draft"  # draft | submitted | approved | rejected | published
    revisions: list[Revision] = []
    comments: list[Comment] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


class PubMatMetadata(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    article_id: int
    asset_url: str
    asset_type: str
    description: str | None = None
    tags: list[str] = []
    uploaded_by: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


def doc_to_dict(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB document _id ObjectId to string."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc
