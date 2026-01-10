from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .routers import auth
import os

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ITmatch", version="1.0.0")

# Подключаем статические файлы
os.makedirs("app/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="app/templates")

# Подключаем роутеры
app.include_router(auth.router)

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    """Главная страница"""
    # Проверяем авторизацию
    user_id = request.cookies.get("user_id")
    if user_id:
        return {"message": "Добро пожаловать в ITmatch!"}
    return {"message": "Добро пожаловать! Пожалуйста, войдите или зарегистрируйтесь."}

# Базовая защита маршрутов
def require_auth(request: Request, db: Session = Depends(get_db)):
    """Защита маршрутов, требующих авторизации"""
    user = auth.get_current_user(request, db)
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return user