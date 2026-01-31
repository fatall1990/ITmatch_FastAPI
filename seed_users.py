#!/usr/bin/env python3
"""
Скрипт для добавления тестовых пользователей в базу данных ITmatch
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import User, Like, Match, Message
from app.crud.users import create_user
from app.schemas import UserCreate
from passlib.context import CryptContext

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt", "django_pbkdf2_sha256"], deprecated="auto")

# Тестовые данные пользователей
TEST_USERS = [
    {
        "username": "Александр Петров",
        "email": "alex@itmatch.ru",
        "password": "alex123",
        "specialization": "Backend",
        "experience": "Senior",
        "bio": "Senior Python разработчик с 8-летним опытом. Специализируюсь на Django, FastAPI и микросервисной архитектуре. Ищу интересные проекты и команду.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Мария Сидорова",
        "email": "maria@itmatch.ru",
        "password": "maria123",
        "specialization": "Frontend",
        "experience": "Middle",
        "bio": "Frontend разработчик (React, Vue.js). Люблю создавать красивые и функциональные интерфейсы. Ищу проект с современным стеком технологий.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Дмитрий Иванов",
        "email": "dmitry@itmatch.ru",
        "password": "dmitry123",
        "specialization": "Fullstack",
        "experience": "Senior",
        "bio": "Fullstack разработчик (Python/JS). Имею опыт в создании стартапов с нуля. Ищу команду для амбициозного проекта.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Екатерина Смирнова",
        "email": "ekaterina@itmatch.ru",
        "password": "ekaterina123",
        "specialization": "Data Science",
        "experience": "Middle",
        "bio": "Data Scientist с фокусом на машинном обучении. Работала с NLP и компьютерным зрением. Ищу команду для исследовательского проекта.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Андрей Кузнецов",
        "email": "andrey@itmatch.ru",
        "password": "andrey123",
        "specialization": "DevOps",
        "experience": "Senior",
        "bio": "DevOps инженер. Настраиваю CI/CD, контейнеризацию, мониторинг. Помогаю командам становиться более эффективными.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Ольга Морозова",
        "email": "olga@itmatch.ru",
        "password": "olga123",
        "specialization": "Mobile",
        "experience": "Junior",
        "bio": "Начинающий iOS разработчик. Завершила курсы, сейчас ищу первую работу или стажировку. Готова к сложным задачам и обучению.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Иван Николаев",
        "email": "ivan@itmatch.ru",
        "password": "ivan123",
        "specialization": "Backend",
        "experience": "Middle",
        "bio": "Backend разработчик на Go и Python. Увлекаюсь высоконагруженными системами. Ищу проект с интересными техническими вызовами.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Анна Павлова",
        "email": "anna@itmatch.ru",
        "password": "anna123",
        "specialization": "Frontend",
        "experience": "Junior",
        "bio": "Junior Frontend разработчик. Изучаю React, TypeScript. Хочу попасть в дружную команду с менторством.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Сергей Васильев",
        "email": "sergey@itmatch.ru",
        "password": "sergey123",
        "specialization": "Data Science",
        "experience": "Senior",
        "bio": "Lead Data Scientist. Управлял командой из 5 человек. Специализация: рекомендательные системы и прогнозная аналитика.",
        "avatar_url": "default_avatar.png"
    },
    {
        "username": "Наталья Федорова",
        "email": "natalya@itmatch.ru",
        "password": "natalya123",
        "specialization": "Fullstack",
        "experience": "Middle",
        "bio": "Fullstack разработчик (Python + Vue.js). Люблю создавать продукты от идеи до продакшена. Ищу проект с социальной значимостью.",
        "avatar_url": "default_avatar.png"
    }
]

# Специализации для случайной генерации
SPECIALIZATIONS = ["Backend", "Frontend", "Fullstack", "Data Science", "DevOps", "Mobile"]
EXPERIENCES = ["Junior", "Middle", "Senior"]
NAMES = ["Алексей", "Дмитрий", "Максим", "Артем", "Владимир", "Евгений", "Михаил",
         "Анна", "Елена", "Ольга", "Татьяна", "Юлия", "Ирина", "Светлана"]
SURNAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев",
            "Федоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов", "Егоров"]
TECHNOLOGIES = ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Swift", "Kotlin"]
BIOS = [
    "Ищу команду для создания инновационного проекта.",
    "Хочу развиваться в интересной сфере IT.",
    "Ищу ментора или команду для совместного роста.",
    "Готов к решению сложных технических задач.",
    "Ищу проект с использованием современных технологий.",
    "Хочу работать над продуктом с реальной пользой для людей.",
    "Ищу команду единомышленников для стартапа.",
    "Готов к релокации для интересного проекта.",
    "Ищу возможность работать удаленно в сильной команде.",
    "Хочу развивать экспертизу в новой для себя области."
]


def create_test_users(count=10, clear_existing=False):
    """Создать тестовых пользователей"""
    db = SessionLocal()

    try:
        if clear_existing:
            print("⚠️  Очистка существующих пользователей...")
            db.query(User).delete()
            db.commit()
            print("✅ Пользователи удалены")

        print(f"🔄 Создание {count} тестовых пользователей...")

        created_users = []

        # Используем предопределенных пользователей
        for i, user_data in enumerate(TEST_USERS[:count], 1):
            try:
                # Создаём схему пользователя
                user_schema = UserCreate(**user_data)

                # Создаём пользователя через CRUD
                user = create_user(db, user_schema)
                created_users.append(user)

                print(f"✅ {i}. Создан: {user.username} ({user.email})")

            except Exception as e:
                print(f"❌ Ошибка при создании пользователя {user_data['email']}: {e}")

        db.commit()

        print(f"\n🎉 Создано {len(created_users)} пользователей")

        # Создаём несколько лайков и совпадений для реалистичности
        if len(created_users) >= 3:
            print("\n🔄 Создание тестовых лайков и совпадений...")
            create_test_likes_and_matches(db, created_users)

        return created_users

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return []
    finally:
        db.close()


def create_test_likes_and_matches(db, users):
    """Создать тестовые лайки и совпадения"""
    try:
        # Создаём лайки между пользователями
        likes_created = 0
        matches_created = 0

        # Первый пользователь лайкает нескольких других
        from_user = users[0]
        for to_user in users[1:4]:  # Лайкает пользователей 2, 3, 4
            # Проверяем, нет ли уже такого лайка
            existing_like = db.query(Like).filter(
                Like.from_user_id == from_user.id,
                Like.to_user_id == to_user.id
            ).first()

            if not existing_like:
                like = Like(
                    from_user_id=from_user.id,
                    to_user_id=to_user.id
                )
                db.add(like)
                likes_created += 1
                print(f"   👍 {from_user.username} → {to_user.username}")

        # Второй пользователь лайкает первого (взаимный лайк = совпадение)
        like_back = Like(
            from_user_id=users[1].id,
            to_user_id=users[0].id
        )
        db.add(like_back)
        likes_created += 1

        # Создаём совпадение для взаимных лайков
        match = Match(
            user1_id=min(users[0].id, users[1].id),
            user2_id=max(users[0].id, users[1].id)
        )
        db.add(match)
        matches_created += 1

        # Добавляем тестовые сообщения в совпадение
        messages = [
            ("Привет! Вижу, мы оба backend разработчики. Есть идеи для совместного проекта?", users[0].id),
            ("Привет! Да, я как раз ищу команду для нового стартапа. Что тебе интересно?", users[1].id),
            ("Мне интересны высоконагруженные системы и микросервисы. У тебя есть опыт в этом?", users[0].id),
        ]

        for text, sender_id in messages:
            message = Message(
                match_id=match.id,
                sender_id=sender_id,
                text=text
            )
            db.add(message)

        db.commit()

        print(f"✅ Создано {likes_created} лайков и {matches_created} совпадений")
        print(f"💬 Добавлено {len(messages)} тестовых сообщений")

    except Exception as e:
        print(f"❌ Ошибка при создании лайков: {e}")
        db.rollback()


def generate_random_user():
    """Сгенерировать случайного пользователя"""
    name = random.choice(NAMES)
    surname = random.choice(SURNAMES)
    username = f"{name} {surname}"
    email = f"{name.lower()}.{surname.lower()}@itmatch.test"
    password = f"{name.lower()}123"
    specialization = random.choice(SPECIALIZATIONS)
    experience = random.choice(EXPERIENCES)
    bio = random.choice(BIOS)

    return {
        "username": username,
        "email": email,
        "password": password,
        "specialization": specialization,
        "experience": experience,
        "bio": bio,
        "avatar_url": "default_avatar.png"
    }


def create_random_users(count=5):
    """Создать случайных пользователей"""
    db = SessionLocal()

    try:
        print(f"🎲 Создание {count} случайных пользователей...")

        for i in range(1, count + 1):
            user_data = generate_random_user()

            try:
                user_schema = UserCreate(**user_data)
                user = create_user(db, user_schema)
                print(f"✅ {i}. Создан: {user.username} ({user.email}) - {user.specialization} {user.experience}")

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print(f"⚠️  Пользователь {user_data['email']} уже существует, пропускаем")
                else:
                    print(f"❌ Ошибка: {e}")

        db.commit()
        print(f"\n🎉 Создано {count} случайных пользователей")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


def list_users():
    """Показать список всех пользователей"""
    db = SessionLocal()

    try:
        users = db.query(User).order_by(User.id).all()

        print(f"\n👥 Список пользователей ({len(users)}):")
        print("=" * 80)
        print(f"{'ID':<4} {'Имя':<20} {'Email':<25} {'Специализация':<15} {'Опыт':<8} {'Админ'}")
        print("-" * 80)

        for user in users:
            admin_flag = "👑" if user.is_admin else ""
            print(
                f"{user.id:<4} {user.username:<20} {user.email:<25} {user.specialization:<15} {user.experience:<8} {admin_flag}")

        print("=" * 80)

        # Статистика
        if users:
            specs = {}
            exps = {}

            for user in users:
                specs[user.specialization] = specs.get(user.specialization, 0) + 1
                exps[user.experience] = exps.get(user.experience, 0) + 1

            print("\n📊 Статистика:")
            print("Специализации:", ", ".join([f"{k}: {v}" for k, v in specs.items()]))
            print("Опыт:", ", ".join([f"{k}: {v}" for k, v in exps.items()]))

    finally:
        db.close()


def set_admin(user_id, is_admin=True):
    """Установить/снять права администратора"""
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            print(f"❌ Пользователь с ID {user_id} не найден")
            return

        old_status = user.is_admin
        user.is_admin = is_admin
        db.commit()

        status = "администратором" if is_admin else "обычным пользователем"
        print(f"✅ Пользователь {user.username} ({user.email}) теперь {status}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


def show_help():
    """Показать справку"""
    print("=" * 60)
    print("Утилита для управления пользователями ITmatch")
    print("=" * 60)
    print("\nИспользование:")
    print("  python seed_users.py create [count]       - создать тестовых пользователей")
    print("  python seed_users.py random [count]       - создать случайных пользователей")
    print("  python seed_users.py list                 - показать всех пользователей")
    print("  python seed_users.py admin <id>           - сделать пользователя администратором")
    print("  python seed_users.py user <id>            - сделать администратора пользователем")
    print("  python seed_users.py clear                - удалить всех пользователей (осторожно!)")
    print("\nПримеры:")
    print("  python seed_users.py create 5             - создать 5 тестовых пользователей")
    print("  python seed_users.py random 3             - создать 3 случайных пользователя")
    print("  python seed_users.py admin 1              - сделать пользователя с ID 1 администратором")
    print("  python seed_users.py list                 - показать список пользователей")


if __name__ == "__main__":
    print("🚀 Запуск утилиты для управления пользователями")

    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        count = 10  # по умолчанию
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
            except:
                print(f"⚠️  Неверное количество: {sys.argv[2]}, использую 10")

        create_test_users(count=count)

    elif command == "random":
        count = 5  # по умолчанию
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
            except:
                print(f"⚠️  Неверное количество: {sys.argv[2]}, использую 5")

        create_random_users(count=count)

    elif command == "list":
        list_users()

    elif command == "admin":
        if len(sys.argv) < 3:
            print("❌ Укажите ID пользователя: python seed_users.py admin <id>")
        else:
            try:
                user_id = int(sys.argv[2])
                set_admin(user_id, True)
            except:
                print(f"❌ Неверный ID: {sys.argv[2]}")

    elif command == "user":
        if len(sys.argv) < 3:
            print("❌ Укажите ID пользователя: python seed_users.py user <id>")
        else:
            try:
                user_id = int(sys.argv[2])
                set_admin(user_id, False)
            except:
                print(f"❌ Неверный ID: {sys.argv[2]}")

    elif command == "clear":
        confirm = input("⚠️  Вы уверены, что хотите удалить ВСЕХ пользователей? (yes/no): ")
        if confirm.lower() == "yes":
            db = SessionLocal()
            try:
                count = db.query(User).count()
                db.query(User).delete()
                db.commit()
                print(f"✅ Удалено {count} пользователей")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print("❌ Операция отменена")

    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()