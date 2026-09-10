from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_mongo import get_mongo_db
from app.core.database_pg import get_db
from app.core.security import get_current_user, require_role
from app.models.sql_models import PublishedArticle, User
from app.schemas.article_schema import ArticleResponse, PublishRequest

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/publish", response_model=ArticleResponse, status_code=201)
async def publish_article(
    payload: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    mongo_db = get_mongo_db()
    draft = await mongo_db["drafts"].find_one({"_id": ObjectId(payload.draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] != "approved":
        raise HTTPException(status_code=400, detail="Only approved drafts can be published")

    article = PublishedArticle(
        title=payload.title,
        draft_id=payload.draft_id,
        author_id=draft["author_id"],
        category_id=payload.category_id,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    await mongo_db["drafts"].update_one({"_id": ObjectId(payload.draft_id)}, {"$set": {"status": "published"}})
    return article


@router.get("", response_model=list[ArticleResponse])
async def list_articles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PublishedArticle))
    return result.scalars().all()


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PublishedArticle).where(PublishedArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "editor")),
):
    result = await db.execute(select(PublishedArticle).where(PublishedArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.delete(article)
    await db.commit()
