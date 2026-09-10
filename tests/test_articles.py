from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database_pg import get_db
from app.core.security import get_current_user
from tests.conftest import EDITOR, JOURNALIST, mock_db


APPROVED_DRAFT = {
    "_id": "507f1f77bcf86cd799439011",
    "title": "Draft Title",
    "content": "Body",
    "author_id": 1,
    "status": "approved",
}

FAKE_ARTICLE = MagicMock()
FAKE_ARTICLE.id = 1
FAKE_ARTICLE.title = "Published"
FAKE_ARTICLE.draft_id = "507f1f77bcf86cd799439011"
FAKE_ARTICLE.author_id = 1
FAKE_ARTICLE.category_id = None
FAKE_ARTICLE.published_at = datetime(2024, 1, 1)


@pytest.fixture
def db():
    session = mock_db()
    session.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=FAKE_ARTICLE),
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[FAKE_ARTICLE]))),
    ))
    session.refresh = AsyncMock(side_effect=lambda obj: (
        setattr(obj, "id", 1) or
        setattr(obj, "published_at", datetime(2024, 1, 1))
    ))
    return session


@pytest.fixture
async def editor_client_with_db(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: EDITOR
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, db
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_publish_article(editor_client_with_db):
    c, db = editor_client_with_db
    mongo_col = MagicMock()
    mongo_col.find_one = AsyncMock(return_value=APPROVED_DRAFT)
    mongo_col.update_one = AsyncMock()

    with patch("app.controllers.article_controller.get_mongo_db", return_value={"drafts": mongo_col}):
        resp = await c.post("/articles/publish", json={
            "draft_id": "507f1f77bcf86cd799439011",
            "title": "Published",
        })
    assert resp.status_code == 201


async def test_publish_non_approved_draft(editor_client_with_db):
    c, _ = editor_client_with_db
    mongo_col = MagicMock()
    mongo_col.find_one = AsyncMock(return_value={**APPROVED_DRAFT, "status": "draft"})

    with patch("app.controllers.article_controller.get_mongo_db", return_value={"drafts": mongo_col}):
        resp = await c.post("/articles/publish", json={
            "draft_id": "507f1f77bcf86cd799439011",
            "title": "Published",
        })
    assert resp.status_code == 400


async def test_list_articles(editor_client_with_db):
    c, _ = editor_client_with_db
    resp = await c.get("/articles")
    assert resp.status_code == 200


async def test_get_article(editor_client_with_db):
    c, _ = editor_client_with_db
    resp = await c.get("/articles/1")
    assert resp.status_code == 200


async def test_get_article_not_found(editor_client_with_db):
    c, db = editor_client_with_db
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    resp = await c.get("/articles/999")
    assert resp.status_code == 404


async def test_delete_article(editor_client_with_db):
    c, _ = editor_client_with_db
    resp = await c.delete("/articles/1")
    assert resp.status_code == 204


async def test_publish_forbidden_for_journalist(client):
    resp = await client.post("/articles/publish", json={
        "draft_id": "507f1f77bcf86cd799439011",
        "title": "Published",
    })
    assert resp.status_code == 403
