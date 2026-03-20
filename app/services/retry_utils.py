from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def run_with_retries(
    operation: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    on_retry: Callable[[int, float], None] | None = None,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 1
    while True:
        try:
            return operation()
        except Exception:
            if attempt >= max_attempts:
                raise
            if on_retry is not None:
                on_retry(attempt, backoff_seconds)
            if backoff_seconds > 0:
                time.sleep(backoff_seconds)
            attempt += 1
