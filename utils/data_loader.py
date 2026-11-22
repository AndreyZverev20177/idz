"""Чтение, валидация и очистка загруженных музыкальных CSV.

Проверяет размер, кодировку и структуру, исключает некорректные строки
и возвращает статистику качества данных через объект ``LoadedData``.
"""

from dataclasses import dataclass
from io import BytesIO

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = (
    "name",
    "genre",
    "artist(s)",
    "monthly_listens_total",
)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class DataValidationError(ValueError):
    """The supplied CSV does not contain analyzable music data."""


@dataclass(frozen=True)
class LoadedData:
    """Validated rows and basic data-quality diagnostics."""

    frame: pd.DataFrame
    total_rows: int
    dropped_rows: int
    missing_values: int
    column_count: int


def read_csv_bytes(content: bytes) -> LoadedData:
    """Load a UTF-8/CP1251 CSV and discard invalid records.

    Valid records have non-empty track, genre and artist fields and a finite,
    non-negative numeric listening count. Parsing never executes file content.
    """
    if not content:
        raise DataValidationError("CSV-файл пуст.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise DataValidationError("Размер CSV-файла превышает 10 МБ.")

    frame = None
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            frame = pd.read_csv(BytesIO(content), encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise DataValidationError("Не удалось прочитать CSV-файл.") from error
    if frame is None:
        raise DataValidationError("Неподдерживаемая кодировка CSV-файла.")

    missing = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing:
        raise DataValidationError(
            "Отсутствуют обязательные столбцы: " + ", ".join(missing)
        )

    total_rows = len(frame)
    missing_values = int(frame.isna().sum().sum())
    cleaned = frame.copy()
    cleaned["monthly_listens_total"] = pd.to_numeric(
        cleaned["monthly_listens_total"], errors="coerce"
    )
    listens = cleaned["monthly_listens_total"].to_numpy(dtype=float)
    valid = np.isfinite(listens) & (listens >= 0)
    for column in ("name", "genre", "artist(s)"):
        valid &= cleaned[column].notna().to_numpy()
        valid &= cleaned[column].astype(str).str.strip().ne("").to_numpy()

    cleaned = cleaned.loc[valid].copy()
    if cleaned.empty:
        raise DataValidationError("В файле нет корректных строк для анализа.")

    return LoadedData(
        frame=cleaned,
        total_rows=total_rows,
        dropped_rows=total_rows - len(cleaned),
        missing_values=missing_values,
        column_count=len(frame.columns),
    )


def load_data(file_path: str) -> pd.DataFrame:
    """Open a local CSV file with the same checks as an uploaded file."""
    with open(file_path, "rb") as file:
        return read_csv_bytes(file.read()).frame
