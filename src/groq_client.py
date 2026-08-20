"""Thin wrapper around the Groq chat-completion API.

Reads the API key from the environment (never hardcoded). Wraps every SDK/
network failure into a single friendly GroqClientError so callers never need
to know about the Groq SDK's exception hierarchy.
"""

import logging
import os

import groq
from groq.types.chat import ChatCompletion

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/gpt-oss-20b"
REQUEST_TIMEOUT_SECONDS = 30.0
# Sized to stay well under this account's free-tier tokens-per-minute limit
# alongside a typical prompt (~1000 tokens), while giving even a 7-day plan
# comfortable room to finish without truncating.
MAX_OUTPUT_TOKENS = 4096
# "low" keeps reasoning-capable models (e.g. openai/gpt-oss-20b) from
# spending most of the token budget on hidden chain-of-thought — without it,
# longer plans were getting truncated before reaching the closing safety
# disclaimer. Not every model supports this parameter, so call_groq falls
# back to omitting it if the model rejects it.
REASONING_EFFORT = "low"

_FRIENDLY_AUTH_ERROR = (
    "We couldn't authenticate with the AI service. Please check that the "
    "GROQ_API_KEY is configured correctly."
)
_FRIENDLY_RATE_LIMIT_ERROR = (
    "The AI service is receiving too many requests right now. Please wait a "
    "moment and try again."
)
_FRIENDLY_TIMEOUT_ERROR = (
    "The AI service took too long to respond. Please try again."
)
_FRIENDLY_CONNECTION_ERROR = (
    "We couldn't reach the AI service. Please check your internet connection "
    "and try again."
)
_FRIENDLY_GENERIC_ERROR = (
    "Something went wrong while generating your plan. Please try again."
)


class GroqClientError(Exception):
    """Raised when the Groq API call fails for any reason.

    The message is always safe to show directly to an end user.
    """


def call_groq(prompt: str, model: str | None = None) -> str:
    """Send a prompt to Groq and return the raw text response.

    The model defaults to the GROQ_MODEL environment variable if set, then
    falls back to DEFAULT_MODEL — Groq's catalog of active models changes
    over time, so the model name should be configurable without a code
    change.

    Raises GroqClientError (with a user-safe message) on any failure —
    missing/invalid API key, network error, timeout, rate limit, or other
    API/service error. The original exception is logged, never re-raised
    directly, so callers can display GroqClientError's message as-is.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqClientError(
            "No Groq API key is configured. Set the GROQ_API_KEY environment "
            "variable and try again."
        )

    resolved_model = model or os.environ.get("GROQ_MODEL") or DEFAULT_MODEL
    client = groq.Groq(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        response = _create_completion(
            client, resolved_model, prompt, with_reasoning_effort=True
        )
    except groq.BadRequestError as exc:
        if not _rejects_reasoning_effort(exc):
            _raise_friendly_error(exc)
        logger.info(
            "Model %s does not support reasoning_effort; retrying without it",
            resolved_model,
        )
        try:
            response = _create_completion(
                client, resolved_model, prompt, with_reasoning_effort=False
            )
        except groq.GroqError as retry_exc:
            _raise_friendly_error(retry_exc)
    except groq.GroqError as exc:
        _raise_friendly_error(exc)

    return _extract_content(response)


def _create_completion(
    client: groq.Groq, model: str, prompt: str, with_reasoning_effort: bool
) -> ChatCompletion:
    kwargs: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
    if with_reasoning_effort:
        kwargs["reasoning_effort"] = REASONING_EFFORT
    return client.chat.completions.create(**kwargs)


def _rejects_reasoning_effort(exc: groq.BadRequestError) -> bool:
    return "reasoning_effort" in str(exc)


def _raise_friendly_error(exc: groq.GroqError) -> None:
    """Log the real exception and raise the matching friendly GroqClientError."""
    if isinstance(exc, groq.AuthenticationError):
        logger.warning("Groq authentication failed: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_AUTH_ERROR) from exc
    if isinstance(exc, groq.RateLimitError):
        logger.warning("Groq rate limit hit: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_RATE_LIMIT_ERROR) from exc
    if isinstance(exc, groq.APITimeoutError):
        logger.warning("Groq request timed out: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_TIMEOUT_ERROR) from exc
    if isinstance(exc, groq.APIConnectionError):
        logger.warning("Groq connection error: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_CONNECTION_ERROR) from exc
    logger.warning("Groq API error: %s", type(exc).__name__)
    raise GroqClientError(_FRIENDLY_GENERIC_ERROR) from exc


def _extract_content(response: ChatCompletion) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        logger.warning("Malformed Groq response shape: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_GENERIC_ERROR) from exc

    return content or ""
