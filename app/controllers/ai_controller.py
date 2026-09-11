from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database_mongo import get_mongo_db
from app.core.security import require_role
from app.models.sql_models import User
from app.services.gemini_service import evaluate_draft

router = APIRouter(prefix="/api/v1/drafts", tags=["AI"])


@router.post("/{draft_id}/evaluate")
async def evaluate(
    draft_id: str,
    _: User = Depends(require_role("editor_in_chief", "associate_editor")),
):
    db = get_mongo_db()
    doc = await db["drafts"].find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    data = {
        "title": doc.get("title"),
        "content": doc.get("content"),
        "status": doc.get("status"),
        "author_id": doc.get("author_id"),
    }
    return await evaluate_draft(data)
