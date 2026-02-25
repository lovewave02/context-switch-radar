import os
from pathlib import Path

from fastapi.testclient import TestClient


os.environ["CSR_DB_PATH"] = str(Path("data/test_context_switch_radar.db"))

from src.backend.main import app  # noqa: E402


def test_events_and_fragmentation_flow():
    client = TestClient(app)

    payloads = [
        {
            "source": "vscode",
            "title": "Implement login",
            "task_key": "task-login",
            "occurred_at": "2026-02-25T10:00:00+00:00",
        },
        {
            "source": "chrome",
            "title": "Read docs",
            "task_key": "task-docs",
            "occurred_at": "2026-02-25T10:03:00+00:00",
        },
        {
            "source": "vscode",
            "title": "Fix tests",
            "task_key": "task-tests",
            "occurred_at": "2026-02-25T10:20:00+00:00",
        },
    ]

    for item in payloads:
        res = client.post('/events', json=item)
        assert res.status_code == 200

    res_events = client.get('/events?limit=10')
    assert res_events.status_code == 200
    assert len(res_events.json()) >= 3

    res_metric = client.get('/metrics/fragmentation?hours=168')
    assert res_metric.status_code == 200
    body = res_metric.json()
    assert body['event_count'] >= 3
    assert body['switch_count'] >= 2
    assert 0 <= body['fragmentation_score'] <= 100
