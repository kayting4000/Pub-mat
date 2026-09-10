from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from tests.conftest import JOURNALIST, EDITOR


SUBMITTED_DOC = {
    "_id": "507f1f77bcf86cd799439011",
    "title": "Test",
    "content": "Body",
    "author_id": 1,
    "status": "submitted",
    "revisions": [],
    "comments": [],
    "created_at": datetime(2024, 1, 1),
    "updated_at": datetime(2024, 1, 1),
}

DRAFT_DOC = {**SUBMITTED_DOC, "status": "draft"}


def mock_col(doc):
    col = MagicMock()
    col.find_one = AsyncMock(return_value=doc)
    col.update_one = AsyncMock()
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[doc] if doc else [])
    col.find = MagicMock(return_value=cursor)
    return col


async def test_submit_draft(client):
    col = mock_col(DRAFT_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await client.post("/submissions/507f1f77bcf86cd799439011/submit")
    assert resp.status_code == 200


async def test_submit_already_submitted(client):
    col = mock_col(SUBMITTED_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await client.post("/submissions/507f1f77bcf86cd799439011/submit")
    assert resp.status_code == 400


async def test_submit_not_owner(editor_client):
    doc = {**DRAFT_DOC, "author_id": 99}
    col = mock_col(doc)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.post("/submissions/507f1f77bcf86cd799439011/submit")
    assert resp.status_code == 403


async def test_list_pending(editor_client):
    col = mock_col(SUBMITTED_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.get("/submissions/pending")
    assert resp.status_code == 200


async def test_list_pending_forbidden(client):
    resp = await client.get("/submissions/pending")
    assert resp.status_code == 403


async def test_review_approve(editor_client):
    col = mock_col(SUBMITTED_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.post(
            "/submissions/507f1f77bcf86cd799439011/review",
            json={"action": "approve"},
        )
    assert resp.status_code == 200


async def test_review_reject_with_comment(editor_client):
    col = mock_col(SUBMITTED_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.post(
            "/submissions/507f1f77bcf86cd799439011/review",
            json={"action": "reject", "comment": "Needs work"},
        )
    assert resp.status_code == 200


async def test_review_invalid_action(editor_client):
    col = mock_col(SUBMITTED_DOC)
    with patch("app.controllers.submission_controller.get_mongo_db", return_value={"drafts": col}):
        resp = await editor_client.post(
            "/submissions/507f1f77bcf86cd799439011/review",
            json={"action": "publish"},
        )
    assert resp.status_code == 400
