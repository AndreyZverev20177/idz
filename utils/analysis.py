"""Расчёты и графики для музыкальных данных.

Функции принимают очищенный DataFrame, не обращаются к интерфейсу
или HTTP-серверу. Это единая бизнес-логика двух точек входа.
"""

import ast
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


def get_data_info(frame: pd.DataFrame) -> dict[str, Any]:
    """Report basic statistics about the already-validated dataset."""
    return {
        "Количество треков": len(frame),
        "Количество столбцов": len(frame.columns),
        "Количество пропусков": int(frame.isna().sum().sum()),
        "Названия столбцов": list(frame.columns),
    }


def get_popular_tracks(
    frame: pd.DataFrame, min_listens: int = 1_000_000
) -> pd.DataFrame:
    """Return tracks at or above the selected monthly listening threshold."""
    filtered = frame.loc[
        frame["monthly_listens_total"] >= min_listens
    ].copy()
    return filtered.sort_values("monthly_listens_total", ascending=False)


def calculate_mean_listens(frame: pd.DataFrame) -> float:
    """Average monthly listens per track."""
    return float(frame["monthly_listens_total"].mean())


def parse_artists(value: Any) -> list[str]:
    """Interpret a list-like CSV cell or a single artist name safely."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        if pd.isna(value):
            return []
        value = str(value)
    value = value.strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (ValueError, SyntaxError, TypeError, RecursionError):
            pass
    return [value]


def get_artist_rating(frame: pd.DataFrame) -> pd.DataFrame:
    """Rank artists by listens (each collaborator gets full track listens)."""
    artists = frame.copy()
    artists["artist(s)"] = artists["artist(s)"].apply(parse_artists)
    artists = artists.explode("artist(s)").dropna(subset=["artist(s)"])
    rating = (
        artists.groupby("artist(s)", as_index=False)
        .agg(
            total_listens=("monthly_listens_total", "sum"),
            tracks_count=("name", "count"),
        )
        .sort_values("total_listens", ascending=False)
    )
    return rating.reset_index(drop=True)


def get_genre_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate tracks and monthly listens by genre."""
    statistics = (
        frame.groupby("genre", as_index=False)
        .agg(
            tracks_count=("name", "count"),
            mean_listens=("monthly_listens_total", "mean"),
            total_listens=("monthly_listens_total", "sum"),
        )
        .sort_values("mean_listens", ascending=False)
    )
    return statistics.reset_index(drop=True)


def plot_genre_popularity(frame: pd.DataFrame) -> plt.Figure:
    """Create a chart of average monthly listens by genre."""
    statistics = get_genre_statistics(frame)
    fig, axis = plt.subplots(figsize=(9, 4.5))
    axis.bar(statistics["genre"], statistics["mean_listens"])
    axis.set_title("Среднее количество прослушиваний по жанрам")
    axis.set_xlabel("Жанр")
    axis.set_ylabel("Прослушиваний в месяц")
    axis.tick_params(axis="x", labelrotation=35)
    fig.tight_layout()
    return fig


def plot_popular_tracks(
    frame: pd.DataFrame, min_listens: int = 1_000_000, top_n: int = 10
) -> plt.Figure:
    """Plot exactly the same threshold used in the on-screen tracks table."""
    popular = get_popular_tracks(frame, min_listens).head(top_n)
    fig, axis = plt.subplots(figsize=(9, 4.5))
    axis.barh(popular["name"], popular["monthly_listens_total"])
    axis.invert_yaxis()
    axis.set_title(f"Топ-{top_n} треков с прослушиваниями от {min_listens:,}")
    axis.set_xlabel("Прослушиваний в месяц")
    fig.tight_layout()
    return fig
