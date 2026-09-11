from datetime import datetime, UTC

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database_mongo import get_mongo_db
from app.core.security import get_current_user
from app.models.mongo_models import doc_to_dict
from app.models.sql_models import User
from app.schemas.draft_schema import DraftCreate, DraftResponse, DraftUpdate

router = APIRouter(prefix="/drafts", tags=["Drafts"])


def _drafts_col(db=None):
    return get_mongo_db()["drafts"]


@router.post("", response_model=DraftResponse, status_code=201)
async def create_draft(payload: DraftCreate, current_user: User = Depends(get_current_user)):
    col = _drafts_col()
    now = datetime.now(UTC)
    doc = {
        "title": payload.title,
        "content": payload.content,
        "author_id": current_user.id,
        "category_id": payload.category_id,
        "status": "draft",
        "revisions": [],
        "comments": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {**doc, "id": doc["_id"]}


@router.get("", response_model=list[DraftResponse])
async def list_drafts(current_user: User = Depends(get_current_user)):
    col = _drafts_col()
    query = {} if current_user.role in ("editor_in_chief", "associate_editor") else {"author_id": current_user.id}
    docs = await col.find(query).to_list(length=100)
    return [{**doc_to_dict(d), "id": str(d["_id"])} for d in docs]


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str, current_user: User = Depends(get_current_user)):
    col = _drafts_col()
    doc = await col.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if current_user.role not in ("editor_in_chief", "associate_editor") and doc["author_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {**doc_to_dict(doc), "id": str(doc["_id"])}


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: str, payload: DraftUpdate, current_user: User = Depends(get_current_user)):
    col = _drafts_col()
    doc = await col.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["author_id"] != current_user.id and current_user.role not in ("editor_in_chief", "associate_editor"):
        raise HTTPException(status_code=403, detail="Access denied")

    revision = {"content": doc["content"], "revised_at": datetime.now(UTC), "revised_by": current_user.id}
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    updates["updated_at"] = datetime.now(UTC)

    await col.update_one(
        {"_id": ObjectId(draft_id)},
        {"$set": updates, "$push": {"revisions": revision}},
    )
    updated = await col.find_one({"_id": ObjectId(draft_id)})
    return {**doc_to_dict(updated), "id": str(updated["_id"])}


@router.delete("/{draft_id}", status_code=204)
async def delete_draft(draft_id: str, current_user: User = Depends(get_current_user)):
    col = _drafts_col()
    doc = await col.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["author_id"] != current_user.id and current_user.role not in ("editor_in_chief", "associate_editor"):
        raise HTTPException(status_code=403, detail="Access denied")
    await col.delete_one({"_id": ObjectId(draft_id)})
