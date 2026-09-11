from bson import ObjectId
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_mongo import get_mongo_db
from app.core.database_pg import get_db
from app.core.security import get_current_user_cookie
from app.models.sql_models import Category, PublishedArticle, PubMatAsset, RoleEnum, User
from app.services.gemini_service import evaluate_draft

router = APIRouter(prefix="/console", tags=["Console"])
templates = Jinja2Templates(directory="app/views")


@router.get("", response_class=HTMLResponse)
async def overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    mongo = get_mongo_db()
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    article_count = (await db.execute(select(func.count()).select_from(PublishedArticle))).scalar()
    category_count = (await db.execute(select(func.count()).select_from(Category))).scalar()
    ai_log_count = await mongo["ai_logs"].count_documents({})
    pending_count = await mongo["drafts"].count_documents({"status": "submitted"})
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "active": "overview",
        "current_user": current_user,
        "pg_stats": {
            "user_count": user_count,
            "article_count": article_count,
            "category_count": category_count,
        },
        "mongo_stats": {
            "ai_log_count": ai_log_count,
            "pending_count": pending_count,
        },
    })


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(
    request: Request,
    current_user: User = Depends(get_current_user_cookie),
):
    return templates.TemplateResponse("docs.html", {
        "request": request,
        "active": "docs",
        "current_user": current_user,
    })


@router.get("/database", response_class=HTMLResponse)
async def database_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    users = (await db.execute(select(User))).scalars().all()
    articles = (await db.execute(select(PublishedArticle))).scalars().all()
    categories = (await db.execute(select(Category))).scalars().all()
    return templates.TemplateResponse("database.html", {
        "request": request,
        "active": "database",
        "current_user": current_user,
        "users": users,
        "articles": articles,
        "categories": categories,
        "roles": [r.value for r in RoleEnum],
    })


@router.post("/database/categories/create")
async def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    db.add(Category(name=name, description=description or None))
    await db.commit()
    return RedirectResponse("/console/database", status_code=303)


@router.post("/database/categories/{category_id}/delete")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat:
        await db.delete(cat)
        await db.commit()
    return RedirectResponse("/console/database", status_code=303)


@router.post("/database/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and role in RoleEnum._value2member_map_:
        user.role = role
        await db.commit()
    return RedirectResponse("/console/database", status_code=303)


@router.post("/database/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    return RedirectResponse("/console/database", status_code=303)


@router.get("/ai", response_class=HTMLResponse)
async def ai_logs_page(
    request: Request,
    current_user: User = Depends(get_current_user_cookie),
):
    mongo = get_mongo_db()
    logs = await mongo["ai_logs"].find().sort("logged_at", -1).to_list(50)
    for log in logs:
        log["_id"] = str(log["_id"])
    drafts = await mongo["drafts"].find({}, {"_id": 1, "title": 1}).to_list(100)
    for d in drafts:
        d["_id"] = str(d["_id"])
    return templates.TemplateResponse("ai_logs.html", {
        "request": request,
        "active": "ai",
        "current_user": current_user,
        "logs": logs,
        "drafts": drafts,
    })


@router.post("/ai/run")
async def run_ai(
    draft_id: str = Form(...),
    current_user: User = Depends(get_current_user_cookie),
):
    mongo = get_mongo_db()
    doc = await mongo["drafts"].find_one({"_id": ObjectId(draft_id)})
    if doc:
        await evaluate_draft({
            "title": doc.get("title"),
            "content": doc.get("content"),
            "status": doc.get("status"),
            "author_id": doc.get("author_id"),
        })
    return RedirectResponse("/console/ai", status_code=303)


@router.get("/security", response_class=HTMLResponse)
async def security_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    admins = (await db.execute(select(User).where(User.role == RoleEnum.editor_in_chief))).scalars().all()
    return templates.TemplateResponse("security.html", {
        "request": request,
        "active": "security",
        "current_user": current_user,
        "admins": admins,
    })


@router.get("/logout")
async def logout():
    response = RedirectResponse("/auth/login-page", status_code=302)
    response.delete_cookie("access_token")
    return response
