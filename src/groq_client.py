"""Thin wrapper around the Groq chat-completion API.

Reads the API key from the environment (never hardcoded). Wraps every SDK/
network failure into a single friendly GroqClientError so callers never need
to know about the Groq SDK's exception hierarchy.
"""

import logging
import os

import groq

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT_SECONDS = 30.0

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


def call_groq(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Groq and return the raw text response.

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

    client = groq.Groq(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except groq.AuthenticationError as exc:
        logger.warning("Groq authentication failed: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_AUTH_ERROR) from exc
    except groq.RateLimitError as exc:
        logger.warning("Groq rate limit hit: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_RATE_LIMIT_ERROR) from exc
    except groq.APITimeoutError as exc:
        logger.warning("Groq request timed out: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_TIMEOUT_ERROR) from exc
    except groq.APIConnectionError as exc:
        logger.warning("Groq connection error: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_CONNECTION_ERROR) from exc
    except groq.APIStatusError as exc:
        logger.warning("Groq API returned an error status: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_GENERIC_ERROR) from exc
    except groq.GroqError as exc:
        logger.warning("Groq SDK error: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_GENERIC_ERROR) from exc

    return _extract_content(response)


def _extract_content(response: object) -> str:
    try:
        choices = response.choices  # type: ignore[attr-defined]
        content = choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        logger.warning("Malformed Groq response shape: %s", type(exc).__name__)
        raise GroqClientError(_FRIENDLY_GENERIC_ERROR) from exc

    return content or ""
