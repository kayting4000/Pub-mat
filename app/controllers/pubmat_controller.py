from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_mongo import get_mongo_db
from app.core.database_pg import get_db
from app.core.security import get_current_user, require_role
from app.models.sql_models import PublishedArticle, PubMatAsset, User
from app.schemas.pubmat_schema import PubMatAttach, PubMatResponse

router = APIRouter(prefix="/pubmats", tags=["PubMats"])


@router.post("/attach/{article_id}", response_model=PubMatResponse, status_code=201)
async def attach_pubmat(
    article_id: int,
    payload: PubMatAttach,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor", "layout_artist")),
):
    result = await db.execute(select(PublishedArticle).where(PublishedArticle.id == article_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Article not found")

    asset = PubMatAsset(
        article_id=article_id,
        asset_url=payload.asset_url,
        asset_type=payload.asset_type,
        uploaded_by=current_user.id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    # Store rich metadata in Mongo
    mongo_db = get_mongo_db()
    await mongo_db["pubmat_metadata"].insert_one({
        "article_id": article_id,
        "asset_url": payload.asset_url,
        "asset_type": payload.asset_type,
        "description": payload.description,
        "tags": payload.tags,
        "uploaded_by": current_user.id,
    })

    return asset


@router.get("/{article_id}", response_model=list[PubMatResponse])
async def get_pubmats(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(PubMatAsset).where(PubMatAsset.article_id == article_id))
    return result.scalars().all()
