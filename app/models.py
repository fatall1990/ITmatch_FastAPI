from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    specialization = Column(String, nullable=False)  # 'Backend', 'Frontend', 'Data Science'
    experience = Column(String, nullable=False)  # 'Junior', 'Middle', 'Senior'
    bio = Column(Text)
    avatar_url = Column(String, default="default_avatar.png")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи с другими таблицами
    sent_likes = relationship("Like", foreign_keys="Like.from_user_id", back_populates="from_user")
    received_likes = relationship("Like", foreign_keys="Like.to_user_id", back_populates="to_user")
    matches1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1")
    matches2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_likes")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_likes")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches2")
    messages = relationship("Message", back_populates="match")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)

    # Связи
    match = relationship("Match", back_populates="messages")
    sender = relationship("User")