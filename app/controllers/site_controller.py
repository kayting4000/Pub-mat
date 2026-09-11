from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_pg import get_db
from app.models.sql_models import Category, PublishedArticle, PubMatAsset

router = APIRouter(prefix="/site", tags=["Site"])
templates = Jinja2Templates(directory="app/views")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    articles = (await db.execute(select(PublishedArticle).order_by(PublishedArticle.published_at.desc()).limit(6))).scalars().all()
    return templates.TemplateResponse("home.html", {"request": request, "articles": articles})


@router.get("/articles", response_class=HTMLResponse, include_in_schema=False)
async def articles_page(request: Request, db: AsyncSession = Depends(get_db)):
    articles = (await db.execute(select(PublishedArticle).order_by(PublishedArticle.published_at.desc()))).scalars().all()
    return templates.TemplateResponse("articles.html", {"request": request, "articles": articles})


@router.get("/articles/{article_id}", response_class=HTMLResponse, include_in_schema=False)
async def article_detail(article_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PublishedArticle).where(PublishedArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    pubmats = (await db.execute(select(PubMatAsset).where(PubMatAsset.article_id == article_id))).scalars().all()
    return templates.TemplateResponse("article_detail.html", {"request": request, "article": article, "pubmats": pubmats})


@router.get("/categories", response_class=HTMLResponse, include_in_schema=False)
async def categories_page(request: Request, db: AsyncSession = Depends(get_db)):
    categories = (await db.execute(select(Category))).scalars().all()
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories})
