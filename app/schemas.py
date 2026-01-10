from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Схемы для пользователей
class UserBase(BaseModel):
    email: EmailStr
    username: str
    specialization: str
    experience: str
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    avatar_url: str
    created_at: datetime

    class Config:
        orm_mode = True


# Схема для аутентификации
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Схема для обновления профиля
class UserUpdate(BaseModel):
    username: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[str] = None
    bio: Optional[str] = None


# Схемы для лайков
class LikeCreate(BaseModel):
    to_user_id: int


# Схемы для сообщений
class MessageCreate(BaseModel):
    text: str
    match_id: int


class Message(BaseModel):
    id: int
    text: str
    sender_id: int
    created_at: datetime
    is_read: bool

    class Config:
        orm_mode = True