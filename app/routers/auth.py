from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register")
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_user(
        request: Request,
        db: Session = Depends(get_db)
):
    """Обработка регистрации пользователя"""
    form = await request.form()

    # Проверяем, существует ли пользователь с таким email
    existing_user = crud.get_user_by_email(db, form.get("email"))
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пользователь с таким email уже существует"
        })

    # Создаём нового пользователя
    user_data = schemas.UserCreate(
        email=form.get("email"),
        username=form.get("username"),
        password=form.get("password"),
        specialization=form.get("specialization"),
        experience=form.get("experience"),
        bio=form.get("bio", "")
    )

    user = crud.create_user(db, user_data)

    # Редирект на страницу входа после успешной регистрации
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.get("/login")
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_user(
        request: Request,
        db: Session = Depends(get_db)
):
    """Обработка входа пользователя"""
    form = await request.form()

    # Ищем пользователя по email
    user = crud.get_user_by_email(db, form.get("email"))

    if not user or not crud.verify_password(form.get("password"), user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный email или пароль"
        })

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Пользователь заблокирован"
        })

    # Успешный вход - создаём сессию
    response = RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    # Используем простую сессию через cookies (для упрощения)
    response.set_cookie(key="user_id", value=str(user.id))
    return response


@router.get("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="user_id")
    return response


# Зависимость для получения текущего пользователя
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Получить текущего пользователя из сессии"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return crud.get_user_by_id(db, int(user_id))