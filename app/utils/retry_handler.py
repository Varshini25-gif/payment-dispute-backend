from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

ResultT = TypeVar("ResultT")


def execute_with_retry(
    operation: Callable[[], ResultT],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.3,
    max_delay_seconds: float = 2.0,
    backoff_multiplier: float = 2.0,
    jitter_seconds: float = 0.1,
    should_retry: Callable[[Exception], bool] | None = None,
    on_retry: Callable[[int, Exception, float], None] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> ResultT:
    """Execute an operation with exponential backoff retry semantics."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 1
    while True:
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001
            is_retryable = should_retry(exc) if should_retry else True
            if attempt >= max_attempts or not is_retryable:
                raise

            delay = min(max_delay_seconds, base_delay_seconds * (backoff_multiplier ** (attempt - 1)))
            if jitter_seconds > 0:
                delay += random.uniform(0.0, jitter_seconds)

            if on_retry is not None:
                on_retry(attempt, exc, delay)

            sleep_fn(delay)
            attempt += 1
