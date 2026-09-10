from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest

from tests.conftest import make_user, JOURNALIST, EDITOR, ADMIN


def fake_user_row(role="journalist", user_id=1):
    u = MagicMock()
    u.id = user_id
    u.username = "testuser"
    u.email = "test@example.com"
    u.role = role
    u.created_at = datetime(2024, 1, 1)
    return u


async def test_get_me(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["role"] == "journalist"


async def test_list_users_as_editor(editor_client):
    resp = await editor_client.get("/users")
    assert resp.status_code == 200


async def test_list_users_forbidden_for_journalist(client):
    resp = await client.get("/users")
    assert resp.status_code == 403


async def test_get_user_by_id(editor_client):
    resp = await editor_client.get("/users/2")
    assert resp.status_code in (200, 404)


async def test_update_role_as_admin(admin_client):
    resp = await admin_client.put("/users/1/role", json={"role": "editor"})
    assert resp.status_code in (200, 404)


async def test_update_role_forbidden(editor_client):
    resp = await editor_client.put("/users/1/role", json={"role": "admin"})
    assert resp.status_code == 403


async def test_delete_user_as_admin(admin_client):
    resp = await admin_client.delete("/users/1")
    assert resp.status_code in (204, 404)


async def test_delete_user_forbidden(client):
    resp = await client.delete("/users/1")
    assert resp.status_code == 403
