"""Отдых вне экспедиции: 6 ч до полного HP (по таймеру воркера)."""

from __future__ import annotations

from typing import Any

REST_DURATION_SEC = 6 * 3600


def new_rest_state(*, now_ts: float) -> dict[str, Any]:
    return {"end_ts": now_ts + REST_DURATION_SEC}
