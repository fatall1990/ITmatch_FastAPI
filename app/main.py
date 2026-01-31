# app/main.py - ПОЛНАЯ ВЕРСИЯ с debug роутами
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .routers import auth, profiles, feed, messages
from .admin import setup_admin
import os
from pathlib import Path
import io
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ITmatch", version="1.0.0")

# Подключаем шаблоны
templates = Jinja2Templates(directory="app/templates")

from fastapi import Request
import time


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирует все входящие запросы"""
    start_time = time.time()

    # Логируем запрос
    print(f"\n🔍 ВХОДЯЩИЙ ЗАПРОС:")
    print(f"   Метод: {request.method}")
    print(f"   Путь: {request.url.path}")
    print(f"   Полный URL: {request.url}")
    print(f"   Query params: {dict(request.query_params)}")
    print(f"   Headers: {{...}}")

    # Выполняем запрос
    response = await call_next(request)

    # Логируем результат
    process_time = time.time() - start_time
    print(f"   Ответ: {response.status_code}")
    print(f"   Время: {process_time:.3f}сек")
    print(f"   Response headers: {{...}}")

    return response


async def sync_session_with_cookies(request: Request, call_next):
    """Синхронизирует сессию с cookies"""
    # Копируем user_id из cookies в сессию, если его там нет
    if "user_id" not in request.session:
        user_id = request.cookies.get("user_id")
        if user_id:
            request.session["user_id"] = user_id

    response = await call_next(request)
    return response


# ВАЖНО: SessionMiddleware должен быть ПЕРВЫМ
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here-change-in-production",
    session_cookie="session",
    max_age=3600 * 24,  # 24 часа
    same_site="lax",
    https_only=False  # Для разработки
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ДЕБАГ РОУТЫ - ДОБАВЬТЕ ЭТО ПЕРЕД КОРНЕВЫМ РОУТОМ
@app.get("/debug/admin-session")
async def debug_admin_session(request: Request):
    """Отладка админ-сессии"""
    return {
        "session": dict(request.session),
        "headers": dict(request.headers),
        "url": str(request.url),
        "method": request.method
    }

@app.post("/debug/test-login")
async def test_login(request: Request):
    """Тестовый вход (имитация формы админки)"""
    form = await request.form()
    return {
        "form_data": dict(form),
        "session_before": dict(request.session)
    }
@app.get("/debug/session")
async def debug_session(request: Request):
    """Отладка сессии"""
    session_data = dict(request.session)
    return {
        "session": session_data,
        "cookies": dict(request.cookies)
    }

@app.get("/debug/set-session")
async def set_session(request: Request):
    """Установить тестовую сессию"""
    request.session.update({"test": "value", "admin": True, "user_id": 1})
    return {"message": "Session set", "session": dict(request.session)}

@app.get("/debug/clear-session")
async def clear_session(request: Request):
    """Очистить сессию"""
    request.session.clear()
    return {"message": "Session cleared"}

@app.get("/debug/test")
async def test_debug():
    return {"message": "Debug works!"}


# Подключаем роутеры
app.include_router(auth.router, tags=["auth"])
app.include_router(profiles.router, tags=["profiles"])
app.include_router(feed.router, tags=["feed"])
app.include_router(messages.router, tags=["messages"])

# Настраиваем админ-панель
admin = setup_admin(app)

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


@app.get("/static/admin-logo.png")
async def get_admin_logo():
    """Логотип для админ-панели"""
    logo_path = "app/static/admin-logo.png"
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    # Возвращаем заглушку, если логотипа нет
    return FileResponse("app/static/default_avatar.png")

