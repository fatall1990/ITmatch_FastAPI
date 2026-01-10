from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.orm import Session
from .. import models, schemas
from passlib.context import CryptContext

# Инициализируем контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    """Получить пользователя по email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """Получить пользователя по ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Создать нового пользователя"""
    hashed_password = pbkdf2_sha256.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        specialization=user.specialization,
        experience=user.experience,
        bio=user.bio
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)

def update_user_profile(db: Session, user_id: int, update_data: dict):
    """Обновить профиль пользователя"""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user