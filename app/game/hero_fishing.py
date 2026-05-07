"""Рыбалка вне экспедиции: 2 ч до возврата с уловом."""

from __future__ import annotations

from typing import Any

FISHING_DURATION_SEC = 2 * 3600


def new_fishing_state(*, now_ts: float) -> dict[str, Any]:
    return {"end_ts": now_ts + FISHING_DURATION_SEC}

