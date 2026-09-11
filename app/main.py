from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.database_mongo import close_mongo, connect_mongo
from app.core.database_pg import close_db, init_db
from app.core.seeder import seed_admin
from app.controllers import (
    ai_controller,
    article_controller,
    auth_controller,
    category_controller,
    console_controller,
    draft_controller,
    pubmat_controller,
    site_controller,
    submission_controller,
    user_controller,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await connect_mongo()
    await seed_admin()
    yield
    await close_db()
    await close_mongo()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(site_controller.router)
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(category_controller.router)
app.include_router(draft_controller.router)
app.include_router(submission_controller.router)
app.include_router(article_controller.router)
app.include_router(pubmat_controller.router)
app.include_router(ai_controller.router)
app.include_router(console_controller.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/site/")
