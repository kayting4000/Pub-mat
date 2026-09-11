from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_pg import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.sql_models import CONSOLE_ROLES, STAFF_ROLES, User
from app.schemas.auth_schema import RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="app/views")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where((User.username == payload.username) | (User.email == payload.email)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login-console")
async def login_console(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    username, password = form.get("username"), form.get("password")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)
    if user.role not in CONSOLE_ROLES:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Console access requires Editor-in-Chief or Associate Editor role"}, status_code=403)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse("/console", status_code=302)
    response.set_cookie("access_token", token, httponly=True)
    return response


@router.post("/login-staff")
async def login_staff(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    username, password = form.get("username"), form.get("password")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)
    if user.role not in STAFF_ROLES:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Staff Portal access requires Writer, Photojournalist, Layout Artist, or Cartoonist role"}, status_code=403)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse("/staff", status_code=302)
    response.set_cookie("access_token", token, httponly=True)
    return response
