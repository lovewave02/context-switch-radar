from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import get_conn, init_db
from .scoring import fragmentation_metrics
from .schemas import (
    ClimateMemoryIn,
    ClimateMemoryOut,
    ClimateStatsOut,
    EventIn,
    EventOut,
    FragmentationOut,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Context Switch Radar API", version="0.2.0", lifespan=lifespan)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/climate-memories", response_model=list[ClimateMemoryOut])
def list_climate_memories(
    year: int | None = Query(default=None, ge=1900, le=2100),
    tag: str | None = Query(default=None),
) -> list[ClimateMemoryOut]:
    where = []
    params: list = []

    if year is not None:
        where.append("substr(memory_date, 1, 4) = ?")
        params.append(str(year))
    if tag:
        where.append("lower(climate_tag) = lower(?)")
        params.append(tag.strip())

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT id, title, note, memory_date, lat, lon, city, climate_tag, feeling, temp_c, created_at
            FROM climate_memories
            {where_clause}
            ORDER BY memory_date DESC, id DESC
            """,
            params,
        ).fetchall()

    return [
        ClimateMemoryOut(
            id=row["id"],
            title=row["title"],
            note=row["note"],
            memory_date=datetime.fromisoformat(row["memory_date"]).date(),
            lat=row["lat"],
            lon=row["lon"],
            city=row["city"],
            climate_tag=row["climate_tag"],
            feeling=row["feeling"],
            temp_c=row["temp_c"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@app.post("/api/climate-memories", response_model=ClimateMemoryOut)
def create_climate_memory(payload: ClimateMemoryIn) -> ClimateMemoryOut:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO climate_memories
            (title, note, memory_date, lat, lon, city, climate_tag, feeling, temp_c)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.note,
                payload.memory_date.isoformat(),
                payload.lat,
                payload.lon,
                payload.city,
                payload.climate_tag,
                payload.feeling,
                payload.temp_c,
            ),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT id, title, note, memory_date, lat, lon, city, climate_tag, feeling, temp_c, created_at
            FROM climate_memories
            WHERE id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()

    return ClimateMemoryOut(
        id=row["id"],
        title=row["title"],
        note=row["note"],
        memory_date=datetime.fromisoformat(row["memory_date"]).date(),
        lat=row["lat"],
        lon=row["lon"],
        city=row["city"],
        climate_tag=row["climate_tag"],
        feeling=row["feeling"],
        temp_c=row["temp_c"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@app.delete("/api/climate-memories/{memory_id}")
def delete_climate_memory(memory_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM climate_memories WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="memory not found")

        conn.execute("DELETE FROM climate_memories WHERE id = ?", (memory_id,))
        conn.commit()

    return {"deleted": memory_id}


@app.get("/api/climate-stats", response_model=ClimateStatsOut)
def climate_stats() -> ClimateStatsOut:
    with get_conn() as conn:
        total_row = conn.execute(
            "SELECT COUNT(*) AS cnt, AVG(temp_c) AS avg_temp FROM climate_memories"
        ).fetchone()
        top_tags_rows = conn.execute(
            """
            SELECT climate_tag AS tag, COUNT(*) AS cnt
            FROM climate_memories
            WHERE climate_tag <> ''
            GROUP BY climate_tag
            ORDER BY cnt DESC
            LIMIT 5
            """
        ).fetchall()
        yearly_rows = conn.execute(
            """
            SELECT substr(memory_date, 1, 4) AS year, COUNT(*) AS cnt
            FROM climate_memories
            GROUP BY year
            ORDER BY year DESC
            """
        ).fetchall()

    return ClimateStatsOut(
        total_count=total_row["cnt"] if total_row else 0,
        avg_temp_c=round(total_row["avg_temp"], 1) if total_row and total_row["avg_temp"] is not None else None,
        top_tags=[{"tag": r["tag"], "count": r["cnt"]} for r in top_tags_rows],
        yearly_counts=[{"year": r["year"], "count": r["cnt"]} for r in yearly_rows],
    )


@app.post("/api/climate-seed")
def climate_seed() -> dict:
    demo = [
        (
            "장마 첫 기록",
            "비가 많이 오던 날, 지하철 출구 앞에서 우산 나눔 받음",
            "2024-07-12",
            37.5665,
            126.9780,
            "Seoul",
            "rain",
            "감성",
            23.5,
        ),
        (
            "폭염 기억",
            "아스팔트 열기가 너무 강해서 저녁 산책 포기",
            "2025-08-03",
            35.1796,
            129.0756,
            "Busan",
            "heatwave",
            "피곤",
            34.2,
        ),
        (
            "초겨울 미세먼지",
            "하늘은 맑아도 공기가 탁해서 마스크 필수",
            "2025-11-26",
            37.4563,
            126.7052,
            "Incheon",
            "dust",
            "주의",
            8.1,
        ),
    ]

    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) AS cnt FROM climate_memories").fetchone()["cnt"]
        if count > 0:
            return {"seeded": 0, "reason": "already has data"}

        conn.executemany(
            """
            INSERT INTO climate_memories
            (title, note, memory_date, lat, lon, city, climate_tag, feeling, temp_c)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo,
        )
        conn.commit()

    return {"seeded": len(demo)}


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

    metrics = fragmentation_metrics(
        [{"task_key": row["task_key"], "occurred_at": row["occurred_at"]} for row in rows]
    )
    return FragmentationOut(**metrics)
