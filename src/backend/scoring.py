from __future__ import annotations

from datetime import datetime
from typing import Iterable


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


def fragmentation_metrics(events: Iterable[dict]) -> dict:
    ordered = sorted(events, key=lambda x: x["occurred_at"])
    if len(ordered) < 2:
        return {
            "event_count": len(ordered),
            "switch_count": 0,
            "rapid_switch_count": 0,
            "fragmentation_score": 0.0,
        }

    switch_count = 0
    rapid_switch_count = 0

    for prev, curr in zip(ordered, ordered[1:]):
        if prev["task_key"] != curr["task_key"]:
            switch_count += 1
            delta_sec = (_parse_iso(curr["occurred_at"]) - _parse_iso(prev["occurred_at"]))
            if delta_sec.total_seconds() <= 300:
                rapid_switch_count += 1

    max_switches = len(ordered) - 1
    switch_ratio = switch_count / max_switches
    rapid_ratio = rapid_switch_count / max_switches
    score = min(100.0, round((switch_ratio * 70 + rapid_ratio * 30) * 100, 2))

    return {
        "event_count": len(ordered),
        "switch_count": switch_count,
        "rapid_switch_count": rapid_switch_count,
        "fragmentation_score": score,
    }
