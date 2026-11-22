"""Модульные тесты аналитических функций из ``utils.analysis``.

Проверяют фильтры, агрегирование исполнителей, средние и графики.
"""

import math

import matplotlib

from utils.analysis import (
    calculate_mean_listens,
    get_artist_rating,
    get_data_info,
    get_genre_statistics,
    get_popular_tracks,
    parse_artists,
    plot_popular_tracks,
)

matplotlib.use("Agg")


def test_get_data_info(sample_data):
    result = get_data_info(sample_data)
    assert result["Количество треков"] == 3
    assert result["Количество столбцов"] == 4
    assert result["Количество пропусков"] == 0


def test_get_popular_tracks(sample_data):
    result = get_popular_tracks(sample_data)
    assert len(result) == 2
    assert result.iloc[0]["monthly_listens_total"] == 2_000_000


def test_threshold_is_inclusive(sample_data):
    result = get_popular_tracks(sample_data, min_listens=500_000)
    assert len(result) == 3


def test_calculate_mean_listens(sample_data):
    assert math.isclose(calculate_mean_listens(sample_data), 1_333_333.333333)


def test_parse_artists():
    assert parse_artists("['Artist A', 'Artist B']") == ["Artist A", "Artist B"]
    assert parse_artists("Solo singer") == ["Solo singer"]
    assert parse_artists(None) == []
    assert parse_artists(float("nan")) == []


def test_parse_artists_never_evaluates_python_code():
    payload = "__import__('os').system('echo must_not_run')"
    assert parse_artists(payload) == [payload]


def test_get_artist_rating(sample_data):
    result = get_artist_rating(sample_data)
    assert result.iloc[0]["artist(s)"] == "Artist B"
    assert result.iloc[0]["total_listens"] == 2_500_000


def test_get_genre_statistics(sample_data):
    result = get_genre_statistics(sample_data)
    assert result.iloc[0]["genre"] == "Pop"
    assert result.iloc[0]["tracks_count"] == 2


def test_plot_respects_selected_threshold(sample_data):
    fig = plot_popular_tracks(sample_data, min_listens=2_000_000, top_n=10)
    assert len(fig.axes[0].patches) == 1
    matplotlib.pyplot.close(fig)
