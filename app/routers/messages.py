from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..database import get_db
from .. import crud
from ..routers.auth import get_current_user
from typing import List, Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Главная страница сообщений - редирект на список чатов
@router.get("/messages")
async def messages_main(request: Request):
    """Главная страница сообщений - редирект на список чатов"""
    return RedirectResponse(url="/messages/list")

@router.get("/messages/list", response_class=HTMLResponse)
async def messages_list(
        request: Request,
        db: Session = Depends(get_db)
):
    """Список всех чатов (совпадений) пользователя"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Получаем все чаты пользователя
    chats = crud.messages.get_user_chats(db, user.id)

    return templates.TemplateResponse("messages_list.html", {
        "request": request,
        "user": user,
        "chats": chats
    })


@router.get("/messages/{match_id}", response_class=HTMLResponse)
async def chat_detail(
        match_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Страница чата с конкретным пользователем"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Проверяем, существует ли матч и есть ли у пользователя доступ к нему
    match = crud.likes.get_match_by_users(db, user.id, match_id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Чат не найден или нет доступа")

    # Определяем собеседника
    other_user_id = match.user2_id if match.user1_id == user.id else match.user1_id
    other_user = crud.users.get_user_by_id(db, other_user_id)

    # Получаем историю сообщений
    messages = crud.messages.get_messages_by_match(db, match_id, limit=50)

    return templates.TemplateResponse("chat_detail.html", {
        "request": request,
        "user": user,
        "other_user": other_user,
        "match": match,
        "messages": messages
    })


@router.post("/messages/{match_id}/send")
async def send_message(
        match_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Отправка сообщения в чат"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Проверяем, существует ли матч и есть ли у пользователя доступ к нему
    match = crud.likes.get_match_by_users(db, user.id, match_id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Чат не найден или нет доступа")

    form = await request.form()
    message_text = form.get("message")

    if not message_text or not message_text.strip():
        # Если сообщение пустое, просто обновляем страницу
        return RedirectResponse(url=f"/messages/{match_id}", status_code=303)

    # Создаём сообщение
    crud.messages.create_message(
        db=db,
        match_id=match_id,
        sender_id=user.id,
        text=message_text.strip()
    )

    # Перенаправляем обратно в чат
    return RedirectResponse(url=f"/messages/{match_id}", status_code=303)


@router.get("/messages/with/{user_id}", response_class=HTMLResponse)
async def chat_with_user(
        user_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """Переход к чату с конкретным пользователем по ID"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    if user.id == user_id:
        return RedirectResponse(url="/messages", status_code=303)

    # Проверяем, есть ли матч между пользователями
    match = crud.likes.get_match_by_users(db, user.id, user_id)

    if not match:
        # Если матча нет, перенаправляем на страницу совпадений
        return RedirectResponse(url="/matches", status_code=303)

    # Перенаправляем в существующий чат
    return RedirectResponse(url=f"/messages/{match.id}", status_code=302)