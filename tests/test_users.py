from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database_pg import get_db
from app.core.security import get_current_user
from tests.conftest import JOURNALIST, EDITOR, ADMIN, make_user, mock_db


def fake_user(role="journalist", user_id=1):
    u = MagicMock()
    u.id = user_id
    u.username = "testuser"
    u.email = "test@example.com"
    u.role = role
    u.created_at = datetime(2024, 1, 1)
    return u


FAKE_USER = fake_user("journalist", 1)


@pytest.fixture
async def client_with_db(request):
    current_user = getattr(request, "param", JOURNALIST)
    db = mock_db(scalar=FAKE_USER, scalars_list=[FAKE_USER])
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: current_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, db
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_get_me(client_with_db):
    c, _ = client_with_db
    resp = await c.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["role"] == "journalist"


async def test_list_users_as_editor():
    db = mock_db(scalars_list=[FAKE_USER])
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: EDITOR
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/users")
    assert resp.status_code == 200
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_list_users_forbidden_for_journalist(client_with_db):
    c, _ = client_with_db
    resp = await c.get("/users")
    assert resp.status_code == 403


async def test_get_user_by_id():
    db = mock_db(scalar=FAKE_USER)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: EDITOR
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/users/1")
    assert resp.status_code == 200
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_update_role_as_admin():
    db = mock_db(scalar=FAKE_USER)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.put("/users/1/role", json={"role": "editor"})
    assert resp.status_code == 200
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_update_role_forbidden(client_with_db):
    c, _ = client_with_db
    resp = await c.put("/users/1/role", json={"role": "admin"})
    assert resp.status_code == 403


async def test_delete_user_as_admin():
    db = mock_db(scalar=FAKE_USER)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.delete("/users/1")
    assert resp.status_code == 204
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_delete_user_forbidden(client_with_db):
    c, _ = client_with_db
    resp = await c.delete("/users/1")
    assert resp.status_code == 403
