from sqlalchemy.orm import Session
from .. import models
from datetime import datetime


def create_message(db: Session, match_id: int, sender_id: int, text: str):
    """Создать новое сообщение"""
    db_message = models.Message(
        match_id=match_id,
        sender_id=sender_id,
        text=text
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages_by_match(db: Session, match_id: int, limit: int = 100):
    """Получить сообщения из матча"""
    messages = db.query(models.Message).filter(
        models.Message.match_id == match_id
    ).order_by(models.Message.created_at).limit(limit).all()

    return messages


def get_user_chats(db: Session, user_id: int):
    """Получить все чаты пользователя"""
    # Получаем все матчи пользователя
    from sqlalchemy import or_
    matches = db.query(models.Match).filter(
        or_(
            models.Match.user1_id == user_id,
            models.Match.user2_id == user_id
        )
    ).all()

    # Для каждого матча получаем последнее сообщение
    chats = []
    for match in matches:
        last_message = db.query(models.Message).filter(
            models.Message.match_id == match.id
        ).order_by(models.Message.created_at.desc()).first()

        # Определяем собеседника
        other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
        other_user = db.query(models.User).filter(models.User.id == other_user_id).first()

        chats.append({
            "match": match,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": 0  # Можно добавить логику подсчёта непрочитанных
        })

    return chats