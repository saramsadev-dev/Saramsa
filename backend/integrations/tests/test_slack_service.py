"""
Unit tests for SlackService.

Covers: OAuth flow, message fetching, normalisation, dedup, and rate-limit retry.
All external calls (Slack API, Cosmos DB) are mocked.
"""

import json
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# We need Django settings configured before importing the service.
# ---------------------------------------------------------------------------
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test-secret-key-for-unit-tests",
        SLACK_CLIENT_ID="test_client_id",
        SLACK_CLIENT_SECRET="test_client_secret",
        SLACK_SIGNING_SECRET="test_signing_secret",
        SLACK_REDIRECT_URI="http://localhost:8000/api/integrations/slack/oauth/callback/",
        FRONTEND_BASE_URL="http://localhost:3000",
        COSMOS_DB_CONFIG={
            "endpoint": "https://fake.documents.azure.com:443/",
            "key": "fakekey==",
            "database_name": "test-db",
            "containers": {"integrations": "integrations", "analysis": "analysis"},
        },
    )

from integrations.services.slack_service import SlackService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def slack_service():
    """Return a SlackService with mocked repo & encryption."""
    with patch("integrations.services.slack_service.IntegrationsRepository") as MockRepo, \
         patch("integrations.services.slack_service.get_encryption_service") as mock_enc:
        mock_enc_inst = MagicMock()
        mock_enc_inst.encrypt_token.return_value = "encrypted_xoxb"
        mock_enc_inst.decrypt_token.return_value = "xoxb-test-token"
        mock_enc.return_value = mock_enc_inst

        svc = SlackService()
        svc.integrations_repo = MockRepo.return_value
        svc.encryption_service = mock_enc_inst
        yield svc


# ---------------------------------------------------------------------------
# 1. test_start_oauth_returns_valid_url
# ---------------------------------------------------------------------------

def test_start_oauth_returns_valid_url(slack_service):
    slack_service.integrations_repo.cosmos_service.create_document = MagicMock()

    url = slack_service.start_oauth("user_123")

    assert "client_id=test_client_id" in url
    assert "scope=" in url
    assert "redirect_uri=" in url
    assert "state=slack_" in url
    slack_service.integrations_repo.cosmos_service.create_document.assert_called_once()


# ---------------------------------------------------------------------------
# 2. test_complete_oauth_stores_encrypted_token
# ---------------------------------------------------------------------------

@patch("integrations.services.slack_service.requests.post")
def test_complete_oauth_stores_encrypted_token(mock_post, slack_service):
    # State doc lookup
    slack_service.integrations_repo.cosmos_service.get_document = MagicMock(
        return_value={"id": "slack_abc", "userId": "user_123", "type": "oauth_state"}
    )
    slack_service.integrations_repo.create_or_update_integration_account = MagicMock(
        return_value={"id": "ia_new", "provider": "slack"}
    )
    slack_service.integrations_repo.cosmos_service.delete_document = MagicMock()

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "ok": True,
        "access_token": "xoxb-test",
        "team": {"id": "T123", "name": "TestTeam"},
    }
    mock_post.return_value = mock_resp

    result = slack_service.complete_oauth("code_xyz", "slack_abc")

    slack_service.encryption_service.encrypt_token.assert_called_with("xoxb-test")
    slack_service.integrations_repo.create_or_update_integration_account.assert_called_once()
    assert result["provider"] == "slack"


# ---------------------------------------------------------------------------
# 3. test_complete_oauth_rejects_invalid_state
# ---------------------------------------------------------------------------

def test_complete_oauth_rejects_invalid_state(slack_service):
    slack_service.integrations_repo.cosmos_service.get_document = MagicMock(
        side_effect=Exception("not found")
    )
    slack_service.integrations_repo.cosmos_service.query_documents = MagicMock(
        return_value=[]
    )

    with pytest.raises(ValueError, match="Invalid or expired OAuth state"):
        slack_service.complete_oauth("code", "bad_state")


# ---------------------------------------------------------------------------
# 4. test_fetch_messages_filters_bots
# ---------------------------------------------------------------------------

@patch("integrations.services.slack_service.SlackService._slack_api_get")
def test_fetch_messages_filters_bots(mock_get, slack_service):
    slack_service._get_bot_token = MagicMock(return_value="xoxb-tok")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "ok": True,
        "messages": [
            {"ts": "1000.1", "text": "human msg", "user": "U1"},
            {"ts": "1000.2", "text": "bot msg", "subtype": "bot_message", "user": "U2"},
            {"ts": "1000.3", "text": "another bot", "bot_id": "B1", "user": "U3"},
            {"ts": "1000.4", "text": "another human", "user": "U4"},
        ],
        "response_metadata": {},
    }
    mock_get.return_value = mock_resp

    msgs = slack_service.fetch_channel_messages("u", "a", "C1")
    assert len(msgs) == 2
    assert msgs[0]["text"] == "human msg"
    assert msgs[1]["text"] == "another human"


# ---------------------------------------------------------------------------
# 5. test_fetch_messages_handles_pagination
# ---------------------------------------------------------------------------

@patch("integrations.services.slack_service.time.sleep")
@patch("integrations.services.slack_service.SlackService._slack_api_get")
def test_fetch_messages_handles_pagination(mock_get, mock_sleep, slack_service):
    slack_service._get_bot_token = MagicMock(return_value="xoxb-tok")

    page1 = MagicMock()
    page1.json.return_value = {
        "ok": True,
        "messages": [{"ts": "1.0", "text": "page1", "user": "U1"}],
        "response_metadata": {"next_cursor": "cursor_abc"},
    }
    page2 = MagicMock()
    page2.json.return_value = {
        "ok": True,
        "messages": [{"ts": "2.0", "text": "page2", "user": "U2"}],
        "response_metadata": {},
    }
    mock_get.side_effect = [page1, page2]

    msgs = slack_service.fetch_channel_messages("u", "a", "C1")
    assert len(msgs) == 2
    assert mock_get.call_count == 2


# ---------------------------------------------------------------------------
# 6. test_normalize_to_feedback_format
# ---------------------------------------------------------------------------

def test_normalize_to_feedback_format(slack_service):
    raw = [
        {"slack_ts": "1700000000.000", "text": "Great product!", "user_id": "U1", "channel_id": "C1", "timestamp": "1700000000.000"},
        {"slack_ts": "1700000001.000", "text": "Needs improvement", "user_id": "U2", "channel_id": "C1", "timestamp": "1700000001.000"},
    ]
    user_names = {"U1": "Alice", "U2": "Bob"}

    feedback = slack_service.normalize_to_feedback(raw, "general", user_names)

    assert len(feedback) == 2
    assert feedback[0]["comment"] == "Great product!"
    assert feedback[0]["source"] == "slack"
    assert feedback[0]["source_id"] == "C1_1700000000.000"
    assert feedback[0]["source_channel"] == "general"
    assert feedback[0]["author"] == "Alice"
    assert "created_at" in feedback[0]

    assert feedback[1]["author"] == "Bob"


# ---------------------------------------------------------------------------
# 7. test_deduplicate_messages
# ---------------------------------------------------------------------------

def test_deduplicate_messages(slack_service):
    existing = {"C1_1.0", "C1_2.0"}
    messages = [
        {"channel_id": "C1", "slack_ts": "1.0", "text": "old"},
        {"channel_id": "C1", "slack_ts": "2.0", "text": "old too"},
        {"channel_id": "C1", "slack_ts": "3.0", "text": "new!"},
    ]

    result = slack_service.deduplicate_messages(messages, existing)
    assert len(result) == 1
    assert result[0]["slack_ts"] == "3.0"


# ---------------------------------------------------------------------------
# 8. test_rate_limit_handling
# ---------------------------------------------------------------------------

@patch("integrations.services.slack_service.time.sleep")
@patch("integrations.services.slack_service.requests.get")
def test_rate_limit_handling(mock_get, mock_sleep, slack_service):
    rate_limited = MagicMock()
    rate_limited.status_code = 429
    rate_limited.headers = {"Retry-After": "2"}

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.json.return_value = {"ok": True, "messages": [], "response_metadata": {}}

    mock_get.side_effect = [rate_limited, ok_resp]

    resp = slack_service._slack_api_get(
        "https://slack.com/api/conversations.history",
        "xoxb-tok",
        {"channel": "C1"},
    )

    assert resp.status_code == 200
    mock_sleep.assert_called_with(2)
