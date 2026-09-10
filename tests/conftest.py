from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database_pg import get_db
from app.core.security import get_current_user
from app.models.sql_models import User, RoleEnum


# --- Shared fake users ---

def make_user(role="journalist", user_id=1):
    u = MagicMock(spec=User)
    u.id = user_id
    u.username = "testuser"
    u.email = "test@example.com"
    u.role = role
    u.created_at = datetime(2024, 1, 1)
    return u


JOURNALIST = make_user("journalist", 1)
EDITOR = make_user("editor", 2)
ADMIN = make_user("admin", 3)
LAYOUT = make_user("layout_artist", 4)


# --- DB session mock ---

def make_execute_result(scalar=None, scalars_list=None):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=scalars_list or [])))
    return result


def mock_db(scalar=None, scalars_list=None):
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=make_execute_result(scalar, scalars_list))
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


# --- Client factory ---

async def make_client(current_user=JOURNALIST, db_session=None):
    if db_session is None:
        db_session = mock_db()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: current_user

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test"), db_session


@pytest.fixture
async def client():
    c, _ = await make_client()
    async with c:
        yield c


@pytest.fixture
async def editor_client():
    c, _ = await make_client(current_user=EDITOR)
    async with c:
        yield c


@pytest.fixture
async def admin_client():
    c, _ = await make_client(current_user=ADMIN)
    async with c:
        yield c


@pytest.fixture
async def layout_client():
    c, _ = await make_client(current_user=LAYOUT)
    async with c:
        yield c
