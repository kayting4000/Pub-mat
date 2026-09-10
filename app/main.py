from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database_mongo import close_mongo, connect_mongo
from app.core.database_pg import close_db, init_db
from app.controllers import (
    article_controller,
    auth_controller,
    category_controller,
    draft_controller,
    pubmat_controller,
    submission_controller,
    user_controller,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await connect_mongo()
    yield
    await close_db()
    await close_mongo()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(category_controller.router)
app.include_router(draft_controller.router)
app.include_router(submission_controller.router)
app.include_router(article_controller.router)
app.include_router(pubmat_controller.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": settings.PROJECT_NAME}
