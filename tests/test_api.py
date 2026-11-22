"""Тесты FastAPI: доступность маршрутов, схема ответов и ошибки клиента.

Используют ``TestClient`` и не требуют запуска отдельного HTTP-сервера.
"""

from fastapi.testclient import TestClient

from main import app
from utils.data_loader import MAX_UPLOAD_BYTES

client = TestClient(app)


def test_health_check():
    assert client.get("/health").json() == {"status": "ok"}


def test_api_contract(sample_csv):
    response = client.post(
        "/api/v1/analyze?min_listens=1500000&top_n=5",
        files={"file": ("tracks.csv", sample_csv, "text/csv")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_rows"] == 3
    assert payload["valid_rows"] == 3
    assert len(payload["popular_tracks"]) == 2
    assert payload["artists"][0]["artist"] == "Artist B"
    assert len(payload["genres"]) == 2


def test_api_rejects_wrong_extension():
    response = client.post(
        "/api/v1/analyze", files={"file": ("tracks.txt", b"hi", "text/plain")}
    )
    assert response.status_code == 400


def test_api_rejects_bad_csv():
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("tracks.csv", b"name\nhello", "text/csv")},
    )
    assert response.status_code == 422


def test_api_rejects_bad_threshold(sample_csv):
    response = client.post(
        "/api/v1/analyze?min_listens=-10",
        files={"file": ("tracks.csv", sample_csv, "text/csv")},
    )
    assert response.status_code == 422


def test_api_rejects_large_upload():
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("tracks.csv", b"x" * (MAX_UPLOAD_BYTES + 1), "text/csv")},
    )
    assert response.status_code == 413


def test_openapi_includes_analyze_endpoint():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/analyze" in schema["paths"]
