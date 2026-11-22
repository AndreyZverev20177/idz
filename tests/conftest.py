"""Общие фикстуры pytest для воспроизводимых проверок.

Один небольшой набор треков используется тестами расчётов и HTTP API.
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Three tracks with two genres and shared artists."""
    return pd.DataFrame(
        {
            "name": ["Track 1", "Track 2", "Track 3"],
            "genre": ["Pop", "Rock", "Pop"],
            "artist(s)": [
                "['Artist A', 'Artist B']",
                "['Artist B']",
                "['Artist C']",
            ],
            "monthly_listens_total": [2_000_000, 500_000, 1_500_000],
        }
    )


@pytest.fixture
def sample_csv(sample_data: pd.DataFrame) -> bytes:
    """CSV bytes suitable for upload and API tests."""
    return sample_data.to_csv(index=False).encode("utf-8")
