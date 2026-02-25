# Architecture

- Event collector pushes normalized events to local API.
- Scoring service aggregates 5-minute buckets.
- Dashboard queries precomputed metrics.
