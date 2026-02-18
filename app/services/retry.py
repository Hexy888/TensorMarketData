# Retry Utilities

from __future__ import annotations
import os
import time
import random
from typing import Callable, TypeVar, Any, Optional

T = TypeVar("T")


def _sleep_backoff(attempt: int, base: float, cap: float):
    """Exponential backoff with jitter."""
    delay = min(cap, base * (2 ** max(attempt - 1, 0)))
    jitter = delay * random.uniform(0.1, 0.25)
    time.sleep(delay + jitter)


def retry_call(
    fn: Callable[[], T],
    *,
    max_retries: int,
    backoff_base: float,
    backoff_cap: float,
    should_retry: Callable[[Exception], bool],
) -> T:
    """Retry wrapper with backoff."""
    last: Optional[Exception] = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last = e
            if attempt >= max_retries or not should_retry(e):
                raise
            _sleep_backoff(attempt, backoff_base, backoff_cap)
    
    raise last or RuntimeError("retry failed")
