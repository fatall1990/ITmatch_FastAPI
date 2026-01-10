from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import shutil
from ..database import get_db
from .. import crud, schemas
from ..routers.auth import get_current_user
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Настройки для загрузки файлов
UPLOAD_DIR = "app/static/uploads"
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}


@router.get("/profile", response_class=HTMLResponse)
async def view_profile(
        request: Request,
        db: Session = Depends(get_db)
):
    """Страница профиля пользователя"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Получаем статистику пользователя
    sent_likes, received_likes = crud.likes.get_user_likes(db, user.id)
    matches = crud.likes.get_user_matches(db, user.id)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "stats": {
            "sent_likes": len(sent_likes),
            "received_likes": len(received_likes),
            "matches": len(matches)
        }
    })


@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_page(
        request: Request,
        db: Session = Depends(get_db)
):
    """Страница редактирования профиля"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("edit_profile.html", {
        "request": request,
        "user": user
    })


@router.post("/profile/edit")
async def update_profile(
        request: Request,
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    form = await request.form()

    update_data = {}
    if form.get("username"):
        update_data["username"] = form.get("username")
    if form.get("specialization"):
        update_data["specialization"] = form.get("specialization")
    if form.get("experience"):
        update_data["experience"] = form.get("experience")
    if form.get("bio"):
        update_data["bio"] = form.get("bio")

    if update_data:
        crud.users.update_user_profile(db, user.id, update_data)

    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.post("/profile/upload-avatar")
async def upload_avatar(
        request: Request,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """Загрузка аватарки"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Проверяем расширение файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return templates.TemplateResponse("edit_profile.html", {
            "request": request,
            "user": user,
            "error": "Недопустимый формат файла. Разрешены: .png, .jpg, .jpeg, .gif"
        })

    # Создаём уникальное имя файла
    import uuid
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Обновляем профиль пользователя
    update_data = {"avatar_url": filename}
    crud.users.update_user_profile(db, user.id, update_data)

    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.get("/user/{user_id}")
async def view_other_profile(
        user_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Просмотр профиля другого пользователя"""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login")

    if current_user.id == user_id:
        return RedirectResponse(url="/profile")

    user = crud.users.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, есть ли матч между пользователями
    match = crud.likes.get_match_by_users(db, current_user.id, user_id)

    return templates.TemplateResponse("view_profile.html", {
        "request": request,
        "user": user,
        "current_user": current_user,
        "is_match": match is not None
    })