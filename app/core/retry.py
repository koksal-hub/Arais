from __future__ import annotations

import time
from typing import Callable, Iterable, Tuple, TypeVar

T = TypeVar("T")


def exponential_backoff(attempt: int, *, base: float = 0.5, factor: float = 2.0, max_delay: float = 30.0) -> float:
    delay = base * (factor ** attempt)
    return min(delay, max_delay)


def retry(
    operation: Callable[[], T],
    *,
    retries: int = 3,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    sleep_func: Callable[[float], None] = time.sleep,
    base_delay: float = 0.5,
) -> T:
    attempt = 0
    while True:
        try:
            return operation()
        except exceptions as exc:  # pragma: no cover - re-raised when limit reached
            if attempt >= retries:
                raise
            delay = exponential_backoff(attempt, base=base_delay)
            sleep_func(delay)
            attempt += 1


__all__ = ["exponential_backoff", "retry"]
