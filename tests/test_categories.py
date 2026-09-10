from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database_pg import get_db
from app.core.security import get_current_user
from tests.conftest import EDITOR, JOURNALIST, mock_db, make_execute_result


FAKE_CAT = MagicMock()
FAKE_CAT.id = 1
FAKE_CAT.name = "Tech"
FAKE_CAT.description = "Technology news"


@pytest.fixture
async def editor_cat_client():
    db = mock_db(scalar=FAKE_CAT, scalars_list=[FAKE_CAT])
    db.refresh = AsyncMock(side_effect=lambda obj: (
        setattr(obj, "id", 1) or setattr(obj, "name", "Tech") or setattr(obj, "description", None)
    ))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: EDITOR
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, db
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def journalist_cat_client():
    db = mock_db(scalar=FAKE_CAT, scalars_list=[FAKE_CAT])
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: JOURNALIST
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_create_category(editor_cat_client):
    c, _ = editor_cat_client
    resp = await c.post("/categories", json={"name": "Tech", "description": "Technology news"})
    assert resp.status_code == 201


async def test_create_category_forbidden(journalist_cat_client):
    resp = await journalist_cat_client.post("/categories", json={"name": "Tech"})
    assert resp.status_code == 403


async def test_list_categories(journalist_cat_client):
    resp = await journalist_cat_client.get("/categories")
    assert resp.status_code == 200


async def test_update_category(editor_cat_client):
    c, _ = editor_cat_client
    resp = await c.put("/categories/1", json={"name": "Updated"})
    assert resp.status_code == 200


async def test_update_category_forbidden(journalist_cat_client):
    resp = await journalist_cat_client.put("/categories/1", json={"name": "Updated"})
    assert resp.status_code == 403


async def test_delete_category(editor_cat_client):
    c, _ = editor_cat_client
    resp = await c.delete("/categories/1")
    assert resp.status_code == 204


async def test_delete_category_forbidden(journalist_cat_client):
    resp = await journalist_cat_client.delete("/categories/1")
    assert resp.status_code == 403
