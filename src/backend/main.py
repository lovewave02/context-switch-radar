from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query

from .db import get_conn, init_db
from .scoring import fragmentation_metrics
from .schemas import EventIn, EventOut, FragmentationOut

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Context Switch Radar API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/events", response_model=EventOut)
def create_event(payload: EventIn) -> EventOut:
    task_key = payload.task_key or payload.title.strip().lower()
    occurred_at = payload.occurred_at.astimezone(timezone.utc).isoformat()

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO events (source, title, task_key, occurred_at)
            VALUES (?, ?, ?, ?)
            """,
            (payload.source, payload.title, task_key, occurred_at),
        )
        conn.commit()

        row = conn.execute(
            "SELECT id, source, title, task_key, occurred_at FROM events WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()

    return EventOut(
        id=row["id"],
        source=row["source"],
        title=row["title"],
        task_key=row["task_key"],
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
    )


@app.get("/events", response_model=list[EventOut])
def list_events(limit: int = Query(default=100, ge=1, le=1000)) -> list[EventOut]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, source, title, task_key, occurred_at
            FROM events
            ORDER BY occurred_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        EventOut(
            id=row["id"],
            source=row["source"],
            title=row["title"],
            task_key=row["task_key"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
        )
        for row in rows
    ]


@app.get("/metrics/fragmentation", response_model=FragmentationOut)
def get_fragmentation(hours: int = Query(default=24, ge=1, le=168)) -> FragmentationOut:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT task_key, occurred_at
            FROM events
            WHERE occurred_at >= ?
            ORDER BY occurred_at ASC
            """,
            (cutoff.isoformat(),),
        ).fetchall()

    metrics = fragmentation_metrics([
        {"task_key": row["task_key"], "occurred_at": row["occurred_at"]}
        for row in rows
    ])
    return FragmentationOut(**metrics)
