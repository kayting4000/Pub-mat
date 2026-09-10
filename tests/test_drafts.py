from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from tests.conftest import JOURNALIST, EDITOR


DRAFT_DOC = {
    "_id": "507f1f77bcf86cd799439011",
    "title": "Test Draft",
    "content": "Hello world",
    "author_id": 1,
    "category_id": None,
    "status": "draft",
    "revisions": [],
    "comments": [],
    "created_at": datetime(2024, 1, 1),
    "updated_at": datetime(2024, 1, 1),
}


def mock_col(doc=None, docs=None):
    col = MagicMock()
    col.insert_one = AsyncMock(return_value=MagicMock(inserted_id="507f1f77bcf86cd799439011"))
    col.find_one = AsyncMock(return_value=doc)
    col.update_one = AsyncMock()
    col.delete_one = AsyncMock()
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=docs or [])
    col.find = MagicMock(return_value=cursor)
    return col


@pytest.fixture
def mongo_patch(request):
    doc = getattr(request, "param", DRAFT_DOC)
    col = mock_col(doc=doc, docs=[doc] if doc else [])
    with patch("app.controllers.draft_controller.get_mongo_db", return_value={"drafts": col}):
        yield col


async def test_create_draft(client, mongo_patch):
    resp = await client.post("/drafts", json={"title": "My Draft", "content": "Body text"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "My Draft"


async def test_list_drafts(client, mongo_patch):
    resp = await client.get("/drafts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_draft_own(client, mongo_patch):
    resp = await client.get("/drafts/507f1f77bcf86cd799439011")
    assert resp.status_code == 200


async def test_get_draft_not_found(client):
    col = mock_col(doc=None)
    with patch("app.controllers.draft_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await client.get("/drafts/507f1f77bcf86cd799439011")
    assert resp.status_code == 404


async def test_update_draft(client, mongo_patch):
    resp = await client.put("/drafts/507f1f77bcf86cd799439011", json={"title": "Updated"})
    assert resp.status_code == 200


async def test_delete_draft(client, mongo_patch):
    resp = await client.delete("/drafts/507f1f77bcf86cd799439011")
    assert resp.status_code == 204


async def test_delete_draft_forbidden(editor_client):
    other_doc = {**DRAFT_DOC, "author_id": 99}
    col = mock_col(doc=other_doc)
    with patch("app.controllers.draft_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.delete("/drafts/507f1f77bcf86cd799439011")
    assert resp.status_code == 204  # editor can delete any draft
