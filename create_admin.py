#!/usr/bin/env python3
"""
Скрипт для создания первого администратора
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import User
from passlib.context import CryptContext

# Контекст для хэширования паролей (такой же как в users.py)
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt", "django_pbkdf2_sha256"], deprecated="auto")


def create_admin_user():
    """Создать администратора"""
    db = SessionLocal()

    try:
        # Проверяем, есть ли уже администраторы
        admin_exists = db.query(User).filter(User.is_admin == True).first()
        if admin_exists:
            print(f"⚠️  Администратор уже существует: {admin_exists.email}")
            return

        # Ищем первого пользователя
        first_user = db.query(User).order_by(User.id).first()

        if first_user:
            # Делаем первого пользователя администратором
            first_user.is_admin = True
            db.commit()
            print(f"✅ Пользователь {first_user.email} назначен администратором")

            print("\n📋 Информация для входа в админку:")
            print(f"   Email: {first_user.email}")
            print(f"   Пароль: ваш текущий пароль")
            print(f"   URL: http://127.0.0.1:8000/admin")
        else:
            print("❌ В базе данных нет пользователей")
            print("\n📋 Создайте пользователя через регистрацию, затем запустите этот скрипт снова")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()


def set_specific_user_as_admin(email, password):
    """Установить конкретного пользователя как администратора"""
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"❌ Пользователь с email {email} не найден")
            return

        # Проверяем пароль
        if not pwd_context.verify(password, user.hashed_password):
            print(f"❌ Неверный пароль для пользователя {email}")
            return

        # Назначаем администратором
        user.is_admin = True
        db.commit()

        print(f"✅ Пользователь {email} назначен администратором")
        print(f"📋 URL админ-панели: http://127.0.0.1:8000/admin")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Настройка администратора ITmatch")
    print("=" * 50)

    if len(sys.argv) == 1:
        # Простой режим: делаем первого пользователя администратором
        create_admin_user()
    elif len(sys.argv) == 3:
        # Расширенный режим: устанавливаем конкретного пользователя
        email = sys.argv[1]
        password = sys.argv[2]
        set_specific_user_as_admin(email, password)
    else:
        print("Использование:")
        print("  python create_admin.py                    - сделать первого пользователя администратором")
        print("  python create_admin.py email password     - установить конкретного пользователя как администратора")

    print("\n📝 Примечание: После назначения прав администратора перезапустите сервер")