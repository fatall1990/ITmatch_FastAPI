from sqlalchemy.orm import Session
from sqlalchemy import or_
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


def get_match_by_users(db: Session, user1_id: int, user2_id: int = None, match_id: int = None):
    """Получить матч между двумя пользователями или по ID матча"""
    if match_id:
        # Ищем матч по ID и проверяем, что пользователь в нём участвует
        match = db.query(models.Match).filter(
            models.Match.id == match_id,
            or_(
                models.Match.user1_id == user1_id,
                models.Match.user2_id == user1_id
            )
        ).first()
        return match
    elif user2_id:
        # Ищем матч между двумя пользователями
        match = db.query(models.Match).filter(
            or_(
                and_(models.Match.user1_id == user1_id, models.Match.user2_id == user2_id),
                and_(models.Match.user1_id == user2_id, models.Match.user2_id == user1_id)
            )
        ).first()
        return match
    return None


def mark_messages_as_read(db: Session, match_id: int, user_id: int):
    """Пометить все сообщения в матче как прочитанные (кроме своих)"""
    db.query(models.Message).filter(
        models.Message.match_id == match_id,
        models.Message.sender_id != user_id,
        models.Message.is_read == False
    ).update({models.Message.is_read: True})
    db.commit()


def get_unread_count(db: Session, user_id: int):
    """Получить количество непрочитанных сообщений пользователя"""
    # Получаем все матчи пользователя
    matches = db.query(models.Match).filter(
        or_(
            models.Match.user1_id == user_id,
            models.Match.user2_id == user_id
        )
    ).all()

    total_unread = 0
    for match in matches:
        unread = db.query(models.Message).filter(
            models.Message.match_id == match.id,
            models.Message.sender_id != user_id,
            models.Message.is_read == False
        ).count()
        total_unread += unread

    return total_unread