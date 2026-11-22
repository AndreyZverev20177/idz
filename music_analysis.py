"""Модуль обратной совместимости со старой структурой проекта.

Повторно экспортирует функции из ``utils``. Не содержит второй копии логики.
"""

from utils.analysis import (
    calculate_mean_listens,
    get_artist_rating,
    get_data_info,
    get_genre_statistics,
    get_popular_tracks,
    parse_artists,
    plot_genre_popularity,
    plot_popular_tracks,
)
from utils.data_loader import load_data

__all__ = [
    "calculate_mean_listens",
    "get_artist_rating",
    "get_data_info",
    "get_genre_statistics",
    "get_popular_tracks",
    "parse_artists",
    "plot_genre_popularity",
    "plot_popular_tracks",
    "load_data",
]
