from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database_mongo import get_mongo_db
from app.core.security import get_current_user, require_role
from app.models.mongo_models import doc_to_dict
from app.models.sql_models import User
from app.schemas.submission_schema import ReviewRequest

router = APIRouter(prefix="/submissions", tags=["Submissions"])


def _col():
    return get_mongo_db()["drafts"]


@router.post("/{draft_id}/submit", status_code=200)
async def submit_draft(draft_id: str, current_user: User = Depends(get_current_user)):
    col = _col()
    doc = await col.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["author_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if doc["status"] != "draft":
        raise HTTPException(status_code=400, detail="Only drafts can be submitted")
    await col.update_one({"_id": ObjectId(draft_id)}, {"$set": {"status": "submitted", "updated_at": datetime.utcnow()}})
    return {"message": "Draft submitted for review"}


@router.get("/pending")
async def list_pending(_: User = Depends(require_role("admin", "editor"))):
    col = _col()
    docs = await col.find({"status": "submitted"}).to_list(length=100)
    return [{**doc_to_dict(d), "id": str(d["_id"])} for d in docs]


@router.post("/{draft_id}/review", status_code=200)
async def review_draft(
    draft_id: str,
    payload: ReviewRequest,
    current_user: User = Depends(require_role("admin", "editor")),
):
    if payload.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    col = _col()
    doc = await col.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["status"] != "submitted":
        raise HTTPException(status_code=400, detail="Draft is not pending review")

    new_status = "approved" if payload.action == "approve" else "rejected"
    update: dict = {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}

    if payload.comment:
        comment = {
            "id": str(ObjectId()),
            "author_id": current_user.id,
            "body": payload.comment,
            "created_at": datetime.utcnow(),
        }
        update["$push"] = {"comments": comment}

    await col.update_one({"_id": ObjectId(draft_id)}, update)
    return {"message": f"Draft {new_status}"}
