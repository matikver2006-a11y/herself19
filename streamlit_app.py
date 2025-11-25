import streamlit as st
import zipfile
import io
import tempfile
from pathlib import Path
import os

from label_final import LabelGenerator, setup_logging

st.set_page_config(
    page_title="Генератор этикеток HERSELF19",
    page_icon="🏷️",
    layout="centered"
)

st.title("🏷️ Генератор этикеток HERSELF19")
st.markdown("---")

@st.cache_resource
def get_generator():
    setup_logging()
    return LabelGenerator()
generator = get_generator()

# ----- Ввод данных -----
st.markdown("### 📝 Состав материалов")
composition = st.text_area(
    "Введите состав:",
    placeholder="Например: 95% Хлопок, 5% Эластан"
)

st.markdown("### 🧺 Правила ухода")
care_type = st.radio(
    "Выберите вариант:",
    options=list(generator.CARE_OPTIONS.keys()),
    format_func=lambda k: generator.CARE_OPTIONS[k]["name"],
    horizontal=True
)

st.markdown("### 📏 Размерная сетка")
size_mode = st.radio(
    "Выберите размеры:",
    options=["all", "custom"],
    format_func=lambda v: "Все размеры" if v == "all" else "Выбрать вручную",
    horizontal=True
)
if size_mode == "custom":
    sizes = st.multiselect("Размеры:", options=generator.SIZES, default=generator.SIZES)
else:
    sizes = generator.SIZES

st.markdown("### 🎨 Цвет этикетки")
color_mode = st.radio(
    "Выберите цвет:",
    options=["both", "white", "black"],
    format_func=lambda v: {"both": "Оба цвета", "white": "Только белые", "black": "Только чёрные"}[v],
    horizontal=True
)
if color_mode == "both":
    colors = list(generator.COLORS.keys())
else:
    colors = [color_mode]

st.info("Этикетки создаются в виде PDF-файлов на основе PNG-изображения — печать будет без ошибок текста!")

# ----- Кнопка генерации -----
st.markdown("---")
if st.button("🚀 Сгенерировать этикетки", type="primary", use_container_width=True):
    if not composition or not sizes or not colors:
        st.error("Пожалуйста, заполните все параметры!")
    else:
        with st.spinner("Создаём этикетки..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                original_output = generator.output_dir
                generator.output_dir = Path(temp_dir) / "output"
                generator.output_dir.mkdir(exist_ok=True)

                count = generator.generate_all_labels(
                    composition=composition,
                    care_type=care_type,
                    sizes=sizes,
                    colors=colors
                )
                
                folder = generator.output_dir / composition
                # ---- Проверка и вывод PDF-файлов ----
                pdf_files = list(folder.glob("*.pdf"))
                st.write("Найдено PDF-файлов:", len(pdf_files))
                for file in pdf_files:
                    st.write(file.name)
                if not pdf_files:
                    st.error("PDF-файлы не найдены! Проверьте работу генератора.")
                elif count > 0:
                    # ---- Архивирование ----
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file_path in pdf_files:
                            zip_file.write(file_path, file_path.name)
                    zip_buffer.seek(0)
                    generator.output_dir = original_output
                    st.success(f"Создано {len(pdf_files)} PDF-этикеток!")
                    st.download_button(
                        label="📥 Скачать этикетки (ZIP)",
                        data=zip_buffer,
                        file_name=f"labels_{composition.replace('/', '_')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                else:
                    st.error("Не удалось создать этикетки. Проверьте исходные файлы-шаблоны.")

st.markdown("---")
st.markdown(
    "<small style='color:#666;'>HERSELF19 Label Generator — онлайн и на телефоне</small>",
    unsafe_allow_html=True
)
