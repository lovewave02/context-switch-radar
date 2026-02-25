# Context Switch Radar

A personal productivity observability tool that detects and visualizes hidden context switches across apps, tabs, and tasks.

## Why this is portfolio-worthy
- Not another CRUD app: it models attention as a graph.
- Demonstrates event pipelines, feature engineering, and UX storytelling.
- Can evolve into a real product for developers/designers.

## Core idea
Collect local activity events (window title changes, tab focus, IDE/git actions) and compute a **Context Fragmentation Score** by hour/day.

## MVP scope
- Local event collector stub
- Timeline + fragmentation heatmap (web dashboard)
- Rule-based "focus break" detector
- Export weekly report

## Tech stack
- Backend: Python + FastAPI
- Frontend: React + Vite
- Storage: SQLite

## Project structure
- `src/backend`: API + scoring logic
- `src/frontend`: dashboard UI
- `docs`: architecture and ADRs
- `tests`: unit tests

## Roadmap
1. Add app-specific connectors (VS Code, Chrome, Slack)
2. Replace rules with sequence model
3. Add privacy-preserving local-only mode by default
