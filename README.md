# Context Switch Radar

A personal productivity observability tool that detects and visualizes hidden context switches across apps, tabs, and tasks.

## Why this is portfolio-worthy
- Not another CRUD app: it models attention as a graph.
- Demonstrates event pipelines, feature engineering, and UX storytelling.
- Can evolve into a real product for developers/designers.

## MVP implemented in this repo
- FastAPI backend with local SQLite storage
- Event ingestion API (`POST /events`)
- Event list API (`GET /events`)
- Fragmentation score API (`GET /metrics/fragmentation`)
- Rule-based score using switch ratio + rapid-switch ratio

## Core idea
Collect local activity events (window title changes, tab focus, IDE/git actions) and compute a **Context Fragmentation Score** by hour/day.

## Tech stack
- Backend: Python + FastAPI
- Storage: SQLite
- Frontend: placeholder (`src/frontend`) for upcoming dashboard

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.backend.main:app --reload
```

Health check:
```bash
curl http://127.0.0.1:8000/health
```

Create event:
```bash
curl -X POST http://127.0.0.1:8000/events \
  -H 'Content-Type: application/json' \
  -d '{
    "source":"vscode",
    "title":"Fix login bug",
    "task_key":"bugfix-login",
    "occurred_at":"2026-02-26T00:10:00+00:00"
  }'
```

Get score:
```bash
curl 'http://127.0.0.1:8000/metrics/fragmentation?hours=24'
```

## Project structure
- `src/backend`: API + scoring logic
- `src/frontend`: dashboard placeholder
- `docs`: architecture docs
- `tests`: API and metric tests

## Roadmap
1. Add activity collectors (VS Code window events, browser tab events)
2. Add hourly heatmap endpoint for dashboard
3. Add sequence-model baseline and compare with rule-based score
4. Add privacy controls and redaction rules for window title data
