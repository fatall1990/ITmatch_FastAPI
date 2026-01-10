from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import not_, and_
from ..database import get_db
from .. import crud, models
from ..routers.auth import get_current_user
from typing import List, Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/feed", response_class=HTMLResponse)
async def feed(
        request: Request,
        specialization: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        db: Session = Depends(get_db)
):
    """Лента анкет пользователей"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Количество анкет на странице
    per_page = 10

    # Получаем ID пользователей, которых уже лайкнул текущий пользователь
    liked_user_ids = [like.to_user_id for like in user.sent_likes]

    # Строим базовый запрос
    query = db.query(models.User).filter(
        models.User.id != user.id,
        models.User.is_active == True,
        not_(models.User.id.in_(liked_user_ids))
    )

    # Применяем фильтры
    if specialization:
        query = query.filter(models.User.specialization == specialization)

    if experience:
        query = query.filter(models.User.experience == experience)

    # Пагинация
    total_users = query.count()
    total_pages = (total_users + per_page - 1) // per_page

    users = query.offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse("feed.html", {
        "request": request,
        "users": users,
        "current_user": user,
        "filters": {
            "specialization": specialization,
            "experience": experience
        },
        "pagination": {
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    })


@router.post("/like/{user_id}")
async def like_user(
        user_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Лайк пользователя"""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login")

    if current_user.id == user_id:
        return RedirectResponse(url="/feed", status_code=400)

    # Создаём лайк
    like, is_match = crud.likes.create_like(db, current_user.id, user_id)

    if like:
        if is_match:
            # Перенаправляем на страницу сообщений при совпадении
            return RedirectResponse(url="/matches", status_code=303)
        else:
            # Возвращаем на ленту
            return RedirectResponse(url="/feed", status_code=303)
    else:
        return RedirectResponse(url="/feed", status_code=400)


@router.post("/skip/{user_id}")
async def skip_user(
        user_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Пропустить пользователя (просто возвращаем на ленту)"""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login")

    # Здесь можно добавить логику для сохранения пропущенных пользователей
    return RedirectResponse(url="/feed", status_code=303)


@router.get("/matches", response_class=HTMLResponse)
async def view_matches(
        request: Request,
        db: Session = Depends(get_db)
):
    """Страница совпадений"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Получаем все совпадения пользователя
    matches = crud.likes.get_user_matches(db, user.id)

    # Для каждого матча получаем информацию о собеседнике
    matches_info = []
    for match in matches:
        other_user_id = match.user2_id if match.user1_id == user.id else match.user1_id
        other_user = crud.users.get_user_by_id(db, other_user_id)

        # Получаем последнее сообщение в матче
        messages = crud.messages.get_messages_by_match(db, match.id, limit=1)
        last_message = messages[-1] if messages else None

        matches_info.append({
            "match": match,
            "other_user": other_user,
            "last_message": last_message
        })

    return templates.TemplateResponse("matches.html", {
        "request": request,
        "user": user,
        "matches": matches_info
    })