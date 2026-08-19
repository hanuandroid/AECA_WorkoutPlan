from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import groq
import httpx
import pytest

from src.groq_client import GroqClientError, call_groq

_FAKE_REQUEST = httpx.Request("POST", "https://api.groq.test/v1/chat/completions")


def _fake_response(text: str) -> SimpleNamespace:
    message = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _mock_client_with_effect(effect: object) -> MagicMock:
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = effect
    return mock_client


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_returns_content_on_success(mock_groq_cls: MagicMock) -> None:
    mock_groq_cls.return_value = _mock_client_with_effect(
        lambda **_: _fake_response("# Weekly Workout Plan")
    )

    result = call_groq("some prompt")

    assert result == "# Weekly Workout Plan"


def test_call_groq_missing_api_key_raises_friendly_error() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(GroqClientError):
            call_groq("some prompt")


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_authentication_failure_is_friendly(
    mock_groq_cls: MagicMock,
) -> None:
    response = httpx.Response(401, request=_FAKE_REQUEST)
    error = groq.AuthenticationError("invalid api key", response=response, body=None)
    mock_groq_cls.return_value = _mock_client_with_effect(error)

    with pytest.raises(GroqClientError):
        call_groq("some prompt")


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_connection_error_is_friendly(mock_groq_cls: MagicMock) -> None:
    error = groq.APIConnectionError(request=_FAKE_REQUEST)
    mock_groq_cls.return_value = _mock_client_with_effect(error)

    with pytest.raises(GroqClientError):
        call_groq("some prompt")


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_timeout_is_friendly(mock_groq_cls: MagicMock) -> None:
    error = groq.APITimeoutError(request=_FAKE_REQUEST)
    mock_groq_cls.return_value = _mock_client_with_effect(error)

    with pytest.raises(GroqClientError):
        call_groq("some prompt")


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_rate_limit_is_friendly(mock_groq_cls: MagicMock) -> None:
    response = httpx.Response(429, request=_FAKE_REQUEST)
    error = groq.RateLimitError("rate limited", response=response, body=None)
    mock_groq_cls.return_value = _mock_client_with_effect(error)

    with pytest.raises(GroqClientError):
        call_groq("some prompt")


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_empty_response_returns_empty_string(
    mock_groq_cls: MagicMock,
) -> None:
    mock_groq_cls.return_value = _mock_client_with_effect(
        lambda **_: _fake_response("")
    )

    result = call_groq("some prompt")

    assert result == ""


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
@patch("src.groq_client.groq.Groq")
def test_call_groq_malformed_response_is_friendly(mock_groq_cls: MagicMock) -> None:
    mock_groq_cls.return_value = _mock_client_with_effect(
        lambda **_: SimpleNamespace(choices=[])
    )

    with pytest.raises(GroqClientError):
        call_groq("some prompt")
