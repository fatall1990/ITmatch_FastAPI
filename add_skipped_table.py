#!/usr/bin/env python3
"""
Добавляет таблицу для хранения пропущенных пользователей
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import sqlite3


def add_skipped_table():
    """Добавить таблицу для пропущенных пользователей"""
    db_path = "./itmatch.db"

    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли таблица skipped_users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skipped_users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("🔄 Создание таблицы skipped_users...")

            # Создаём таблицу
            cursor.execute('''
                CREATE TABLE skipped_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    skipped_user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (skipped_user_id) REFERENCES users (id)
                )
            ''')

            # Создаём индекс для быстрого поиска
            cursor.execute('''
                CREATE INDEX idx_skipped_users 
                ON skipped_users (user_id, skipped_user_id)
            ''')

            conn.commit()
            print("✅ Таблица skipped_users создана")
        else:
            print("ℹ️  Таблица skipped_users уже существует")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    add_skipped_table()