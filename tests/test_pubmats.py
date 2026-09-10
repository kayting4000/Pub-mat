from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database_pg import get_db
from app.core.security import get_current_user
from tests.conftest import LAYOUT, JOURNALIST, mock_db


FAKE_ASSET = MagicMock()
FAKE_ASSET.id = 1
FAKE_ASSET.article_id = 1
FAKE_ASSET.asset_url = "http://example.com/img.png"
FAKE_ASSET.asset_type = "image"
FAKE_ASSET.uploaded_by = 4
FAKE_ASSET.uploaded_at = datetime(2024, 1, 1)


@pytest.fixture
def db():
    session = mock_db()
    session.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=MagicMock()),
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[FAKE_ASSET]))),
    ))
    session.refresh = AsyncMock(side_effect=lambda obj: None)
    return session


@pytest.fixture
async def layout_client_with_db(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: LAYOUT
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, db
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


async def test_attach_pubmat(layout_client_with_db):
    c, db = layout_client_with_db
    db.refresh = AsyncMock(side_effect=lambda obj: (
        setattr(obj, "id", 1) or
        setattr(obj, "uploaded_at", datetime(2024, 1, 1))
    ))

    mongo_col = MagicMock()
    mongo_col.insert_one = AsyncMock()

    with patch("app.controllers.pubmat_controller.get_mongo_db", return_value={"pubmat_metadata": mongo_col}):
        resp = await c.post("/pubmats/attach/1", json={
            "asset_url": "http://example.com/img.png",
            "asset_type": "image",
        })
    assert resp.status_code == 201


async def test_attach_pubmat_article_not_found(layout_client_with_db):
    c, db = layout_client_with_db
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    mongo_col = MagicMock()
    mongo_col.insert_one = AsyncMock()

    with patch("app.controllers.pubmat_controller.get_mongo_db", return_value={"pubmat_metadata": mongo_col}):
        resp = await c.post("/pubmats/attach/999", json={
            "asset_url": "http://example.com/img.png",
            "asset_type": "image",
        })
    assert resp.status_code == 404


async def test_get_pubmats(layout_client_with_db):
    c, _ = layout_client_with_db
    resp = await c.get("/pubmats/1")
    assert resp.status_code == 200


async def test_attach_forbidden_for_journalist(client):
    resp = await client.post("/pubmats/attach/1", json={
        "asset_url": "http://example.com/img.png",
        "asset_type": "image",
    })
    assert resp.status_code == 403
