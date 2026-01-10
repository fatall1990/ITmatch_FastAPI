from PIL import Image, ImageDraw, ImageFont
import os


def create_default_avatar():
    """Создаёт дефолтную аватарку"""
    # Путь к дефолтной аватарке
    avatar_path = "app/static/default_avatar.png"

    # Создаём директорию если её нет
    os.makedirs(os.path.dirname(avatar_path), exist_ok=True)

    # Создаём изображение 150x150 пикселей
    img = Image.new('RGB', (150, 150), color='#007bff')  # Синий цвет

    # Рисуем инициалы
    draw = ImageDraw.Draw(img)

    try:
        # Пробуем использовать шрифт (для Windows)
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        # Если шрифт не найден, используем стандартный
        font = ImageFont.load_default()

    # Рисуем вопросительный знак по центру
    text = "?"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (150 - text_width) // 2
    y = (150 - text_height) // 2

    draw.text((x, y), text, font=font, fill='white')

    # Сохраняем изображение
    img.save(avatar_path)
    print(f"✅ Создана дефолтная аватарка: {avatar_path}")

    # Создаём папку для загрузок
    uploads_dir = "app/static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    print(f"✅ Создана папка для загрузок: {uploads_dir}")


if __name__ == "__main__":
    create_default_avatar()