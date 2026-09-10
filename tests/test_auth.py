from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database_pg import get_db
from tests.conftest import mock_db


@pytest.fixture
def db():
    return mock_db()


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, db
    app.dependency_overrides.pop(get_db, None)


async def test_register_success(client):
    c, db = client
    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.role = "journalist"

    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1) or setattr(u, "role", "journalist"))

    with patch("app.controllers.auth_controller.hash_password", return_value="hashed"):
        with patch("app.controllers.auth_controller.create_access_token", return_value="tok"):
            resp = await c.post("/auth/register", json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
            })

    assert resp.status_code == 201
    assert resp.json()["access_token"] == "tok"


async def test_register_duplicate(client):
    c, db = client
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock())))

    resp = await c.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    })

    assert resp.status_code == 400


async def test_login_success(client):
    c, db = client
    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.role = "journalist"
    fake_user.hashed_password = "hashed"

    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=fake_user)))

    with patch("app.controllers.auth_controller.verify_password", return_value=True):
        with patch("app.controllers.auth_controller.create_access_token", return_value="tok"):
            resp = await c.post("/auth/login", data={"username": "alice", "password": "secret123"})

    assert resp.status_code == 200
    assert resp.json()["access_token"] == "tok"


async def test_login_invalid_credentials(client):
    c, db = client
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    resp = await c.post("/auth/login", data={"username": "nobody", "password": "wrong"})

    assert resp.status_code == 401
