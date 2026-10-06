"""Small callback-based helper for collecting eventually available result sets."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

Payload = dict[str, Any]


def rows_from_payload(payload: Any) -> list[Any]:
    """Return rows from common list or dictionary response shapes."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("records", "results", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def payload_is_ready(payload: Any, *, minimum_rows: int = 3) -> bool:
    """Treat an empty response as incomplete so it can be retried."""
    return len(rows_from_payload(payload)) >= minimum_rows


@dataclass(frozen=True)
class CollectionResult:
    payloads: dict[str, Payload]
    attempts: dict[str, int]
    unresolved: tuple[str, ...]


def collect_in_passes(
    keys: Iterable[str],
    *,
    load_cached: Callable[[str], Payload | None],
    fetch: Callable[[str], Payload],
    save_ready: Callable[[str, Payload], None],
    retry_delays: tuple[float, ...] = (0.0, 1.0, 3.0),
    between_requests: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    on_attempt: Callable[[str, int, bool], None] | None = None,
) -> CollectionResult:
    """Retry incomplete items in queue-wide passes and cache only ready results.

    Callbacks keep networking, persistence, and progress reporting outside this
    helper. Duplicate keys are removed while preserving their original order.
    """
    ordered_keys = list(dict.fromkeys(keys))
    payloads: dict[str, Payload] = {}
    attempts = {key: 0 for key in ordered_keys}
    pending: list[str] = []

    for key in ordered_keys:
        cached = load_cached(key)
        if payload_is_ready(cached):
            payloads[key] = cached  # type: ignore[assignment]
        else:
            pending.append(key)

    for delay in retry_delays:
        if not pending:
            break
        if delay > 0:
            sleep(delay)

        still_pending: list[str] = []
        for index, key in enumerate(pending):
            payload = fetch(key)
            attempts[key] += 1
            ready = payload_is_ready(payload)
            if on_attempt is not None:
                on_attempt(key, attempts[key], ready)
            if ready:
                save_ready(key, payload)
                payloads[key] = payload
            else:
                still_pending.append(key)
            if between_requests > 0 and index + 1 < len(pending):
                sleep(between_requests)
        pending = still_pending

    return CollectionResult(
        payloads=payloads,
        attempts=attempts,
        unresolved=tuple(pending),
    )
