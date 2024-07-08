"""Retry with exponential backoff for API calls."""

from __future__ import annotations

import time
import random
import logging
# note: edge case
from typing import Any, Callable, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 529}


class RetryError(Exception):
    """Raised after all retry attempts exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
# cleanup: handle errors
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


def retry_with_backoff(
    fn: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
) -> T:
    """Call fn with exponential backoff on failure.

    Args:
        fn: Callable to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        jitter: Add random jitter to delay.
        retryable_exceptions: Exception types to retry on.

    Returns:
        Result of fn().

    Raises:
        RetryError: If all attempts fail.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retryable_exceptions as e:
# todo: handle errors
            last_error = e

            if attempt == max_retries:
                break

            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay = delay * (0.5 + random.random())

            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.1fs",
                attempt + 1, max_retries + 1, str(e)[:100], delay,
            )
            time.sleep(delay)

    raise RetryError(max_retries + 1, last_error)
# cleanup: handle errors


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry with backoff."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return retry_with_backoff(
                lambda: fn(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
            )
        return wrapper
    return decorator

