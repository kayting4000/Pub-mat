from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import EDITOR, JOURNALIST


FAKE_CAT = MagicMock()
FAKE_CAT.id = 1
FAKE_CAT.name = "Tech"
FAKE_CAT.description = "Technology news"


async def test_create_category(editor_client):
    resp = await editor_client.post("/categories", json={"name": "Tech", "description": "Technology news"})
    assert resp.status_code in (201, 200)


async def test_create_category_forbidden(client):
    resp = await client.post("/categories", json={"name": "Tech"})
    assert resp.status_code == 403


async def test_list_categories(client):
    resp = await client.get("/categories")
    assert resp.status_code == 200


async def test_update_category(editor_client):
    resp = await editor_client.put("/categories/1", json={"name": "Updated"})
    assert resp.status_code in (200, 404)


async def test_update_category_forbidden(client):
    resp = await client.put("/categories/1", json={"name": "Updated"})
    assert resp.status_code == 403


async def test_delete_category(editor_client):
    resp = await editor_client.delete("/categories/1")
    assert resp.status_code in (204, 404)


async def test_delete_category_forbidden(client):
    resp = await client.delete("/categories/1")
    assert resp.status_code == 403
