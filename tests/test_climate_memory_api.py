import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ["CSR_DB_PATH"] = str(Path("/tmp") / f"test_climate_memory_{uuid4().hex}.db")

from src.backend.main import app


def test_climate_memory_crud_and_stats():
    client = TestClient(app)

    create = client.post(
        '/api/climate-memories',
        json={
            'title': '폭염 기록',
            'note': '체감온도가 높아 야외활동을 줄임',
            'memory_date': '2025-08-10',
            'lat': 37.5665,
            'lon': 126.9780,
            'city': 'Seoul',
            'climate_tag': 'heatwave',
            'feeling': 'tired',
            'temp_c': 33.2,
        },
    )
    assert create.status_code == 200
    item = create.json()
    assert item['id'] > 0

    listing = client.get('/api/climate-memories')
    assert listing.status_code == 200
    assert len(listing.json()) >= 1

    stats = client.get('/api/climate-stats')
    assert stats.status_code == 200
    assert stats.json()['total_count'] >= 1

    delete = client.delete(f"/api/climate-memories/{item['id']}")
    assert delete.status_code == 200
