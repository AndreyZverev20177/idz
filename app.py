"""Веб-интерфейс Streamlit для анализа музыкального CSV.

Принимает файл пользователя, вызывает общие функции из пакета ``utils``
и показывает рассчитанные таблицы и графики. API для этого не требуется.
"""

import matplotlib.pyplot as plt
import streamlit as st

from utils.analysis import (
    calculate_mean_listens,
    get_artist_rating,
    get_genre_statistics,
    get_popular_tracks,
    plot_genre_popularity,
    plot_popular_tracks,
)
from utils.data_loader import DataValidationError, read_csv_bytes

st.set_page_config(page_title="Анализ музыкальных треков", page_icon="🎵", layout="wide")
st.title("🎵 Анализ музыкальных треков")
st.write("Загрузите CSV, чтобы сравнить популярность треков, исполнителей и жанров.")

with st.expander("Какие столбцы нужны в CSV?"):
    st.code("name,genre,artist(s),monthly_listens_total")
    st.caption("Максимальный размер файла: 10 МБ. Кодировки UTF-8 и CP1251.")

uploaded_file = st.file_uploader("CSV с музыкальными данными", type=["csv"])
if uploaded_file is None:
    st.info("Для начала анализа загрузите CSV-файл.")
    st.stop()

try:
    loaded = read_csv_bytes(uploaded_file.getvalue())
except DataValidationError as error:
    st.error(str(error))
    st.stop()

frame = loaded.frame
st.success(f"Загружено корректных строк: {len(frame)}")
if loaded.dropped_rows:
    st.warning(f"Исключено строк с пропусками или ошибками: {loaded.dropped_rows}")

st.header("1. Обзор данных")
column1, column2, column3, column4 = st.columns(4)
column1.metric("Треков", len(frame))
column2.metric("Столбцов", loaded.column_count)
column3.metric("Пропусков в исходном файле", loaded.missing_values)
column4.metric("Исключённых строк", loaded.dropped_rows)
st.dataframe(frame.head(20), use_container_width=True)

st.header("2. Популярные треки")
st.metric("Среднее прослушиваний в месяц", f"{calculate_mean_listens(frame):,.0f}")
max_listens = int(frame["monthly_listens_total"].max())
threshold = st.number_input(
    "Минимальное число прослушиваний",
    min_value=0,
    max_value=max_listens,
    value=min(1_000_000, max_listens),
    step=100_000,
)
popular = get_popular_tracks(frame, threshold)
if popular.empty:
    st.info("Треков с выбранным порогом не найдено.")
else:
    st.dataframe(
        popular[["name", "artist(s)", "genre", "monthly_listens_total"]],
        use_container_width=True,
    )
    figure = plot_popular_tracks(frame, min_listens=threshold)
    st.pyplot(figure)
    plt.close(figure)

st.header("3. Рейтинг исполнителей")
st.caption("В совместных треках каждое имя получает полное число прослушиваний.")
st.dataframe(get_artist_rating(frame).head(10), use_container_width=True)

st.header("4. Анализ жанров")
st.dataframe(get_genre_statistics(frame), use_container_width=True)
figure = plot_genre_popularity(frame)
st.pyplot(figure)
plt.close(figure)
