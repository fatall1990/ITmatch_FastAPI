from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .routers import auth, profiles, feed
import os
from pathlib import Path
import io

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ITmatch", version="1.0.0")

# Подключаем статические файлы
os.makedirs("app/static/uploads", exist_ok=True)


def create_default_avatar_if_needed():
    """Создаёт дефолтную аватарку если её нет"""
    default_avatar_path = Path("app/static/default_avatar.png")

    if not default_avatar_path.exists():
        # Создаём простую аватарку
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (150, 150), color='#007bff')
            d = ImageDraw.Draw(img)

            # Рисуем инициалы или символ
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("arial.ttf", 60)
                d.text((75, 75), "?", fill='white', anchor='mm', font=font)
            except:
                d.text((75, 75), "?", fill='white', anchor='mm')

            img.save(default_avatar_path)
            print(f"✅ Создана дефолтная аватарка: {default_avatar_path}")
        except ImportError:
            # Если PIL не установлен, создадим позже через эндпоинт
            print("⚠️  PIL не установлен. Дефолтная аватарка будет создана при первом запросе.")
            # Можно установить: pip install pillow


# Создаём дефолтную аватарку при запуске
create_default_avatar_if_needed()
# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="app/templates")

# Подключаем роутеры
app.include_router(auth.router, tags=["auth"])
app.include_router(profiles.router, tags=["profiles"])
app.include_router(feed.router, tags=["feed"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    # Получаем пользователя из cookies
    from .database import SessionLocal
    from .routers.auth import get_current_user

    db = SessionLocal()
    try:
        user = get_current_user(request, db)

        if user:
            # Если пользователь авторизован, показываем ленту
            return RedirectResponse(url="/feed")
        else:
            # Иначе показываем страницу приветствия
            return templates.TemplateResponse("welcome.html", {
                "request": request,
                "user": None  # Явно передаем None
            })
    finally:
        db.close()

@app.get("/static/default_avatar.png")
async def get_default_avatar():
    """Генерирует дефолтную аватарку если её нет"""
    from fastapi.responses import Response
    import io

    # Создаём простую аватарку
    try:
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (150, 150), color='#007bff')
        d = ImageDraw.Draw(img)
        d.text((75, 75), "?", fill='white', anchor='mm')

        # Конвертируем в bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
    except:
        # Возвращаем пустое изображение
        return Response(content=b"", media_type="image/png")