"""
Генератор этикеток для бренда одежды herself19

✅ ФИНАЛЬНАЯ ВЕРСИЯ С ГИБКОЙ НАСТРОЙКОЙ:

- Легко менять позиции размера и состава
- Отдельные смещения для ONE SIZE
- Полная поддержка кириллицы
- Высокое качество 1064px @ 300DPI
- УВЕЛИЧЕННЫЙ БОС ТЕКСТА СОСТАВА
- ✅ ВСЕ ВАРИАНТЫ -> PNG -> PDF (текст конвертируется в вектор)

Требования: Python 3.8+, Pillow, reportlab

"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
import logging

try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import inch, mm
except ImportError:
    print("Ошибка: reportlab не установлен")
    print("Установите: pip install reportlab pillow")
    sys.exit(1)

# Настройка логирования
def setup_logging(log_file='label_generator.log'):
    """Настраивает логирование"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class LabelGenerator:
    """Класс для генерации этикеток в высоком качестве"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.WORKING_SIZE = 1064  # размер для работы (высокое качество)
        self.FINAL_SIZE_MM = 35   # финальный размер в мм
        self.DPI = 300            # DPI для печати
        self.PX_PER_MM = self.DPI / 25.4
        self.FINAL_SIZE_PX = int(self.FINAL_SIZE_MM * self.PX_PER_MM)
        self.SCALE_FACTOR = self.FINAL_SIZE_PX / self.WORKING_SIZE
        
        self.logger.info(f"Инициализация LabelGenerator ВЫСОКОЕ КАЧЕСТВО")
        self.logger.info(f"Рабочий размер: {self.WORKING_SIZE}x{self.WORKING_SIZE}px")
        self.logger.info(f"Финальный размер: {self.FINAL_SIZE_MM}mm @ {self.DPI}DPI")
        
        # Размеры одежды
        self.SIZES = ['36', '38', '40', '42', '44', '46', '48', 'ONE SIZE']
        
        # Цвета
        self.COLORS = {
            'white': {'name': 'белый', 'text_color': (0, 0, 0)},
            'black': {'name': 'чёрный', 'text_color': (255, 255, 255)}
        }
        
        # Варианты ухода
        self.CARE_OPTIONS = {
            'washable': {
                'name': 'стирать можно',
                'templates': {
                    'white': 'Group-307.jpg',
                    'black': 'Group-308.jpg'
                }
            },
            'not_washable': {
                'name': 'стирать нельзя',
                'templates': {
                    'white': 'Group-305.jpg',
                    'black': 'Group-306.jpg'
                }
            }
        }
        
        # Параметры шрифтов
        self.FONT_SIZES = {
            'size_large': 180,
            'size_small': 120,
            'composition': 40,
            'line_spacing_composition': 30,  # × 1.5 = 45px
            'line_spacing_onesize': 120
        }
        
        # ✅ БАЗОВЫЕ КООРДИНАТЫ (центры текста)
        self.BASE_COORDINATES = {
            'size': {
                'x': 80,   # базовое значение
                'y': 470,  # базовое значение
            },
            'composition': {
                'x': 750,
                'y': 420,
            }
        }
        
        # ✅ СМЕЩЕНИЯ ДЛЯ ОБЫЧНЫХ РАЗМЕРОВ (36-48)
        self.SIZE_OFFSET = {
            'right': -5,   # пиксели вправо
            'up': -47      # пиксели вверх
        }
        
        # ✅ ОТДЕЛЬНЫЕ СМЕЩЕНИЯ ДЛЯ ONE SIZE
        self.SIZE_OFFSET_ONE_SIZE = {
            'right': -32,  # пиксели вправо
            'up': -15      # пиксели вверх
        }
        
        self.COMPOSITION_OFFSET = {
            'right': 50,   # пиксели вправо
            'down': 20     # пиксели вниз
        }
        
        # ✅ БОС ТЕКСТА СОСТАВА
        self.COMPOSITION_BOX = {
            'width': 380,
            'height': 240
        }
        
        # Применяем смещения к базовым координатам
        self.COORDINATES = self._apply_offsets()
        
        # 📁 ВЫХОДНАЯ ДИРЕКТОРИЯ
        self.output_dir = Path('output_labels')
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"📐 Координаты размера: x={self.COORDINATES['size']['x']}, y={self.COORDINATES['size']['y']}")
        self.logger.info(f"📐 Координаты ONE SIZE: x={self.COORDINATES['size_one_size']['x']}, y={self.COORDINATES['size_one_size']['y']}")
        self.logger.info(f"📐 Координаты состава: x={self.COORDINATES['composition']['x']}, y={self.COORDINATES['composition']['y']}")
        self.logger.info(f"📦 Размер бокса состава: {self.COMPOSITION_BOX['width']}x{self.COMPOSITION_BOX['height']}px")

    def _apply_offsets(self):
        """Применяет смещения к базовым координатам"""
        coords = {}
        
        # Размер обычный: базовая позиция + смещение
        coords['size'] = {
            'x': self.BASE_COORDINATES['size']['x'] + self.SIZE_OFFSET['right'],
            'y': self.BASE_COORDINATES['size']['y'] - self.SIZE_OFFSET['up'],
        }
        
        # ✅ Размер ONE SIZE: отдельные смещения
        coords['size_one_size'] = {
            'x': self.BASE_COORDINATES['size']['x'] + self.SIZE_OFFSET_ONE_SIZE['right'],
            'y': self.BASE_COORDINATES['size']['y'] - self.SIZE_OFFSET_ONE_SIZE['up'],
        }
        
        # Состав: базовая позиция + смещение
        coords['composition'] = {
            'x': self.BASE_COORDINATES['composition']['x'] + self.COMPOSITION_OFFSET['right'],
            'y': self.BASE_COORDINATES['composition']['y'] + self.COMPOSITION_OFFSET['down'],
        }
        
        return coords

    def parse_composition(self, composition_input):
        """Парсит строку состава в формат: "50% МАТЕРИАЛ1" """
        if not composition_input:
            self.logger.warning("Состав пуст")
            return []
        
        materials = [m.strip() for m in composition_input.split(',')]
        formatted_materials = []
        
        for material in materials:
            parts = material.split('%', 1)
            if len(parts) == 2:
                percentage = parts[0].strip()
                material_name = parts[1].strip()
                formatted_materials.append(f"{percentage}% {material_name.upper()}")
            else:
                formatted_materials.append(material.upper())
        
        self.logger.debug(f"Распарсено материалов: {len(formatted_materials)}")
        return formatted_materials[:5]

    def load_font(self, size):
        """Загружает шрифт с автоматическим fallback"""
        font_options = [
            "montserrat-bold.ttf",
            "arial.ttf",
            "/Library/Fonts/Helvetica.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, size)
                self.logger.debug(f"✅ Использован шрифт: {font_path} ({size}pt)")
                return font
            except:
                continue
        
        self.logger.warning(f"⚠️ Шрифт не найден, используется стандартный PIL")
        return ImageFont.load_default()

    def create_label_image(self, template_path, size, composition, color):
        """Создаёт этикетку в высоком качестве - ВОЗВРАЩАЕТ ОБЪЕКТ Image"""
        try:
            self.logger.debug(f"Загрузка шаблона: {template_path}")
            template = Image.open(template_path)
            label = template.convert('RGB')
            label = label.resize((self.WORKING_SIZE, self.WORKING_SIZE), Image.Resampling.LANCZOS)
            self.logger.debug(f"Шаблон масштабирован до {self.WORKING_SIZE}x{self.WORKING_SIZE}")
            
            draw = ImageDraw.Draw(label)
            text_color = self.COLORS[color]['text_color']
            
            # Загружаем шрифты
            if size == 'ONE SIZE':
                font_size = int(self.FONT_SIZES['size_small'])
            else:
                font_size = int(self.FONT_SIZES['size_large'])
            
            font_size_text = self.load_font(font_size)
            font_composition = self.load_font(int(self.FONT_SIZES['composition']))
            
            # ==================== РАЗМЕР ====================
            if size == 'ONE SIZE':
                size_coords = self.COORDINATES['size_one_size']
            else:
                size_coords = self.COORDINATES['size']
            
            size_x = size_coords['x']
            size_y = size_coords['y']
            
            if size == 'ONE SIZE':
                draw.text((size_x, size_y), "ONE", fill=text_color, font=font_size_text)
                line_spacing = int(self.FONT_SIZES['line_spacing_onesize'])
                draw.text((size_x, size_y + line_spacing), "SIZE", fill=text_color, font=font_size_text)
                self.logger.debug(f"Написан размер: ONE SIZE в позиции ({size_x}, {size_y})")
            else:
                draw.text((size_x, size_y), size, fill=text_color, font=font_size_text)
                self.logger.debug(f"Написан размер: {size} в позиции ({size_x}, {size_y})")
            
            # ==================== СОСТАВ ВЕРТИКАЛЬНЫЙ (90° вправо) ====================
            comp_coords = self.COORDINATES['composition']
            
            vert_width = self.COMPOSITION_BOX['width']
            vert_height = self.COMPOSITION_BOX['height']
            bg_color = (255, 255, 255) if text_color == (0, 0, 0) else (0, 0, 0)
            
            text_img = Image.new('RGB', (vert_width, vert_height), color=bg_color)
            text_draw = ImageDraw.Draw(text_img)
            
            line_spacing = int(self.FONT_SIZES['line_spacing_composition'] * 1.5)
            
            # Заголовок и материалы
            composition_text = self.parse_composition(composition)
            text_draw.text((10, 10), "СОСТАВ:", fill=text_color, font=font_composition)
            self.logger.debug(f"Написан заголовок: СОСТАВ:")
            
            y_pos = 10 + line_spacing
            for i, material in enumerate(composition_text):
                text_draw.text((10, y_pos), material, fill=text_color, font=font_composition)
                self.logger.debug(f"Строка {i+1}: {material}")
                y_pos += line_spacing
            
            # Поворот на 90° вправо
            text_img_rotated = text_img.rotate(-90, expand=True)
            
            # Вставляем повёрнутый текст с применённым смещением
            vert_x = comp_coords['x']
            vert_y = comp_coords['y']
            label.paste(text_img_rotated, (vert_x, vert_y))
            
            self.logger.info(f"✅ Этикетка создана (размер: {size}, цвет: {color})")
            return label
            
        except FileNotFoundError as e:
            self.logger.error(f"❌ Файл не найден: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Ошибка при создании этикетки: {e}", exc_info=True)
            return None

    def image_to_png(self, image, output_path):
        """Преобразует PIL Image в PNG"""
        try:
            self.logger.debug(f"Сохраняю PNG: {output_path}")
            image.save(output_path, 'PNG', quality=100)
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка при сохранении PNG: {e}")
            return False

    def png_to_pdf(self, png_path, pdf_output_path):
        """Преобразует PNG в высокое качество PDF (как изображение)"""
        try:
            self.logger.debug(f"Начинаю сохранение PNG в PDF: {pdf_output_path}")
            
            c = rl_canvas.Canvas(
                str(pdf_output_path), 
                pagesize=(
                    self.FINAL_SIZE_MM * 2.834645669,
                    self.FINAL_SIZE_MM * 2.834645669
                )
            )
            
            c.drawImage(
                str(png_path), 
                0, 0,
                width=self.FINAL_SIZE_MM * 2.834645669,
                height=self.FINAL_SIZE_MM * 2.834645669
            )
            c.save()
            self.logger.debug(f"✅ PDF сохранён: {pdf_output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при преобразовании PNG в PDF: {e}", exc_info=True)
            return False

    def generate_all_labels(self, composition, care_type, sizes=None, colors=None):
        """Генирует все комбинации этикеток: PNG -> PDF"""
        if sizes is None:
            sizes = self.SIZES
        if colors is None:
            colors = list(self.COLORS.keys())
        
        self.logger.info(f"Начало генерации этикеток")
        self.logger.info(f"Состав: {composition}")
        self.logger.info(f"Правила ухода: {self.CARE_OPTIONS[care_type]['name']}")
        self.logger.info(f"Размеры: {', '.join(sizes)}")
        self.logger.info(f"Цвета: {', '.join([self.COLORS[c]['name'] for c in colors])}")
        
        composition_folder = self.output_dir / composition
        composition_folder.mkdir(exist_ok=True)
        
        # Папка для временных PNG файлов
        png_temp_folder = composition_folder / "_temp_png"
        png_temp_folder.mkdir(exist_ok=True)
        
        generated_count = 0
        error_count = 0
        
        care_templates = self.CARE_OPTIONS[care_type]['templates']
        
        self.logger.info("=" * 70)
        self.logger.info("ЭТАП 1: Создание PIL-изображений и сохранение как PNG")
        self.logger.info("=" * 70)
        
        # ЭТАП 1: Создаём все варианты этикеток как PNG
        png_files = []
        for size in sizes:
            for color in colors:
                template_path = care_templates.get(color)
                if not template_path:
                    self.logger.warning(f"Шаблон для цвета '{color}' не найден")
                    error_count += 1
                    continue
                
                # Создаём PIL-изображение
                label = self.create_label_image(
                    template_path=template_path,
                    size=size,
                    composition=composition,
                    color=color
                )
                
                if label is None:
                    error_count += 1
                    continue
                
                color_name = self.COLORS[color]['name']
                filename_base = f"{composition}_{size}_{color_name}"
                png_path = png_temp_folder / f"{filename_base}.png"
                
                # Сохраняем как PNG
                if self.image_to_png(label, str(png_path)):
                    png_files.append((png_path, filename_base))
                    self.logger.info(f"✅ PNG создана: {filename_base}.png")
                else:
                    error_count += 1
        
        self.logger.info("=" * 70)
        self.logger.info("ЭТАП 2: Преобразование PNG -> PDF")
        self.logger.info("=" * 70)
        
        # ЭТАП 2: Преобразуем все PNG в PDF
        for png_path, filename_base in png_files:
            pdf_filename = f"{filename_base}.pdf"
            pdf_output_path = composition_folder / pdf_filename
            
            if self.png_to_pdf(str(png_path), str(pdf_output_path)):
                self.logger.info(f"✅ PDF создана: {pdf_filename}")
                generated_count += 1
            else:
                error_count += 1
        
        # Удаляем временную папку с PNG
        try:
            import shutil
            shutil.rmtree(png_temp_folder)
            self.logger.debug("Временная папка с PNG удалена")
        except Exception as e:
            self.logger.warning(f"Не удалось удалить временную папку: {e}")
        
        self.logger.info("=" * 70)
        self.logger.info(f"Генерация завершена! ✅ {generated_count} | ❌ {error_count}")
        self.logger.info("=" * 70)
        
        return generated_count

    def run_interactive(self):
        """Интерактивный режим программы"""
        print("\n" + "="*70)
        print("🏷️ ГЕНЕРАТОР ЭТИКЕТОК HERSELF19")
        print("="*70)
        
        print("\n📝 Введите состав материалов")
        print(" Формат: XX% Материал1, YY% Материал2")
        print(" Пример: 95% Хлопок, 5% Эластан")
        composition = input("\nВаш состав: ").strip()
        
        if not composition:
            print("❌ Состав не может быть пустым!")
            return
        
        print("\n🧺 Выберите вариант правил ухода:")
        print(" 1 - Стирать можно")
        print(" 2 - Стирать нельзя")
        care_choice = input("\nВаш выбор (1 или 2): ").strip()
        care_type = 'washable' if care_choice == '1' else 'not_washable'
        
        print("\n📏 Какие размеры генерировать?")
        print(" 0 - Все размеры")
        print(" 1 - Выбрать конкретные")
        sizes_choice = input("\nВаш выбор (0 или 1): ").strip()
        
        if sizes_choice == '1':
            sizes_input = input(" Введите размеры через запятую: ").strip()
            selected_sizes = [s.strip() for s in sizes_input.split(',')]
            sizes = [s for s in selected_sizes if s in self.SIZES]
        else:
            sizes = self.SIZES
        
        print("\n🎨 Какие цвета генерировать?")
        print(" 0 - Оба цвета")
        print(" 1 - Только белый")
        print(" 2 - Только чёрный")
        color_choice = input("\nВаш выбор (0, 1 или 2): ").strip()
        
        color_mapping = {'0': ['white', 'black'], '1': ['white'], '2': ['black']}
        colors = color_mapping.get(color_choice, ['white', 'black'])
        
        print("\n⏳ Генерирую этикетки...")
        count = self.generate_all_labels(composition, care_type, sizes, colors)
        
        print(f"\n{'='*70}")
        print(f"✅ Готово! Создано {count} этикеток")
        print(f"📁 Папка: {(self.output_dir / composition).absolute()}")
        print("="*70 + "\n")

def main():
    logger = setup_logging()
    logger.info("╔════════════════════════════════════════════════════════════════════════╗")
    logger.info("║ ГЕНЕРАТОР ЭТИКЕТОК HERSELF19 - НОВАЯ ВЕРСИЯ                           ║")
    logger.info("║ ║")
    logger.info("║ ✅ ИСПРАВЛЕНО: ║")
    logger.info("║ - Сначала создаются все варианты (PIL Image) ║")
    logger.info("║ - Затем сохраняются как PNG (текст растеризуется) ║")
    logger.info("║ - Потом PNG преобразуется в PDF как изображение ║")
    logger.info("║ - Готов к печати без проблем с текстовыми слоями! ║")
    logger.info("╚════════════════════════════════════════════════════════════════════════╝")
    
    generator = LabelGenerator()
    generator.run_interactive()

if __name__ == "__main__":
    main()
