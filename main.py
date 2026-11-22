"""Точка входа в HTTP API: ``uvicorn main:app``.

Определяет модели JSON-ответа и два маршрута: проверку состояния и анализ CSV.
Расчёты выполняются общими функциями из пакета ``utils``.
"""

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from utils.analysis import (
    calculate_mean_listens,
    get_artist_rating,
    get_genre_statistics,
    get_popular_tracks,
)
from utils.data_loader import (
    MAX_UPLOAD_BYTES,
    DataValidationError,
    read_csv_bytes,
)

app = FastAPI(
    title="Music Analytics API",
    version="1.0.0",
    description="Анализ загруженной CSV-таблицы музыкальных треков.",
)


class Track(BaseModel):
    """One track in the popularity ranking."""

    name: str
    genre: str
    artists: str = Field(description="Исходное поле artist(s) из CSV")
    monthly_listens_total: float


class Artist(BaseModel):
    """An aggregated artist ranking entry."""

    artist: str
    total_listens: float
    tracks_count: int


class Genre(BaseModel):
    """Aggregated data for a genre."""

    genre: str
    total_listens: float
    mean_listens: float
    tracks_count: int


class AnalysisResponse(BaseModel):
    """Documented JSON contract of the analytics endpoint."""

    total_rows: int
    valid_rows: int
    dropped_rows: int
    missing_values: int
    average_listens: float
    popular_tracks: list[Track]
    artists: list[Artist]
    genres: list[Genre]


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    """Liveness check for local development or container monitoring."""
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["analysis"])
async def analyze(
    file: UploadFile = File(description="CSV с музыкальными треками"),
    min_listens: int = Query(default=1_000_000, ge=0),
    top_n: int = Query(default=10, ge=1, le=100),
) -> AnalysisResponse:
    """Validate a CSV file and return typed statistics and leaderboards."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Нужен файл .csv")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV больше 10 МБ")
    try:
        loaded = read_csv_bytes(content)
    except DataValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    frame = loaded.frame
    top = get_popular_tracks(frame, min_listens).head(top_n)
    artist_rating = get_artist_rating(frame).head(top_n)
    genre_statistics = get_genre_statistics(frame)

    return AnalysisResponse(
        total_rows=loaded.total_rows,
        valid_rows=len(frame),
        dropped_rows=loaded.dropped_rows,
        missing_values=loaded.missing_values,
        average_listens=calculate_mean_listens(frame),
        popular_tracks=[
            Track(
                name=str(row["name"]),
                genre=str(row["genre"]),
                artists=str(row["artist(s)"]),
                monthly_listens_total=float(row["monthly_listens_total"]),
            )
            for _, row in top.iterrows()
        ],
        artists=[
            Artist(
                artist=str(row["artist(s)"]),
                total_listens=float(row["total_listens"]),
                tracks_count=int(row["tracks_count"]),
            )
            for _, row in artist_rating.iterrows()
        ],
        genres=[
            Genre(
                genre=str(row["genre"]),
                total_listens=float(row["total_listens"]),
                mean_listens=float(row["mean_listens"]),
                tracks_count=int(row["tracks_count"]),
            )
            for _, row in genre_statistics.iterrows()
        ],
    )
