from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .. import models
from datetime import datetime


def create_like(db: Session, from_user_id: int, to_user_id: int):
    """Создать лайк и проверить на взаимность"""
    # Проверяем, не существует ли уже лайк
    existing_like = db.query(models.Like).filter(
        models.Like.from_user_id == from_user_id,
        models.Like.to_user_id == to_user_id
    ).first()

    if existing_like:
        return None, False  # Лайк уже существует

    # Создаём новый лайк
    db_like = models.Like(
        from_user_id=from_user_id,
        to_user_id=to_user_id
    )
    db.add(db_like)

    # Проверяем на взаимный лайк
    mutual_like = db.query(models.Like).filter(
        models.Like.from_user_id == to_user_id,
        models.Like.to_user_id == from_user_id
    ).first()

    if mutual_like:
        # Создаём матч (совпадение)
        db_match = models.Match(
            user1_id=min(from_user_id, to_user_id),
            user2_id=max(from_user_id, to_user_id)
        )
        db.add(db_match)
        db.commit()
        db.refresh(db_match)
        return db_like, True  # Лайк + матч созданы
    else:
        db.commit()
        db.refresh(db_like)
        return db_like, False  # Только лайк создан


def get_user_likes(db: Session, user_id: int):
    """Получить все лайки пользователя (отправленные и полученные)"""
    sent_likes = db.query(models.Like).filter(
        models.Like.from_user_id == user_id
    ).all()

    received_likes = db.query(models.Like).filter(
        models.Like.to_user_id == user_id
    ).all()

    return sent_likes, received_likes


def get_user_matches(db: Session, user_id: int):
    """Получить все совпадения пользователя"""
    matches = db.query(models.Match).filter(
        or_(
            models.Match.user1_id == user_id,
            models.Match.user2_id == user_id
        )
    ).all()

    return matches


def get_match_by_users(db: Session, user1_id: int, user2_id: int):
    """Получить матч между двумя пользователями"""
    match = db.query(models.Match).filter(
        or_(
            and_(models.Match.user1_id == user1_id, models.Match.user2_id == user2_id),
            and_(models.Match.user1_id == user2_id, models.Match.user2_id == user1_id)
        )
    ).first()

    return match