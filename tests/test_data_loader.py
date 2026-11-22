"""Тесты валидации CSV и отчёта о качестве данных.

Проверяют пропуски, обязательные столбцы, кодировку, размер и ошибки.
"""

import pytest

from utils.data_loader import (
    MAX_UPLOAD_BYTES,
    DataValidationError,
    read_csv_bytes,
)


def test_load_valid_csv(sample_csv):
    result = read_csv_bytes(sample_csv)
    assert result.total_rows == 3
    assert result.dropped_rows == 0
    assert len(result.frame) == 3


def test_missing_columns():
    with pytest.raises(DataValidationError, match="обязательные столбцы"):
        read_csv_bytes(b"name,genre\na,b\n")


def test_empty_csv():
    with pytest.raises(DataValidationError, match="пуст"):
        read_csv_bytes(b"")


def test_invalid_rows_are_dropped():
    content = (
        "name,genre,artist(s),monthly_listens_total\n"
        "Track 1,Pop,Artist A,200\n"
        "Track 2,Pop,Artist B,-1\n"
        "Track 3,Pop,Artist C,not_a_number\n"
        "Track 4,Pop,Artist D,100\n"
    ).encode()
    loaded = read_csv_bytes(content)
    assert loaded.total_rows == 4
    assert loaded.dropped_rows == 2
    assert len(loaded.frame) == 2


def test_no_valid_rows():
    content = (
        "name,genre,artist(s),monthly_listens_total\n"
        "Track 1,Pop,Artist A,invalid\n"
    ).encode()
    with pytest.raises(DataValidationError, match="нет корректных"):
        read_csv_bytes(content)


def test_too_large_csv():
    with pytest.raises(DataValidationError, match="превышает"):
        read_csv_bytes(b"x" * (MAX_UPLOAD_BYTES + 1))


def test_cp1251_file():
    content = (
        "name,genre,artist(s),monthly_listens_total\n"
        "Песня,Поп,Певец,123\n"
    ).encode("cp1251")
    assert read_csv_bytes(content).frame.iloc[0]["name"] == "Песня"
