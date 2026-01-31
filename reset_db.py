#!/usr/bin/env python3
"""
Скрипт для очистки базы данных (только для тестирования!)
"""
import os
import sys
import sqlite3


def reset_database():
    """Очистить базу данных"""
    db_path = "./itmatch.db"

    if os.path.exists(db_path):
        print(f"⚠️  ВНИМАНИЕ: Вы собираетесь удалить базу данных: {db_path}")
        print("   Это удалит ВСЕХ пользователей, лайки, сообщения и т.д.")

        confirmation = input("\n❓ Продолжить? (yes/no): ")

        if confirmation.lower() == "yes":
            try:
                os.remove(db_path)
                print(f"✅ База данных удалена: {db_path}")

                # Создаём новую пустую базу
                print("🔄 Создание новой базы данных...")

                # Импортируем и создаём таблицы
                from app.database import engine, Base
                from app.models import User, Like, Match, Message

                Base.metadata.create_all(bind=engine)
                print("✅ Таблицы созданы успешно")

                print("\n📋 Дальнейшие действия:")
                print("1. Перезапустите сервер: python run.py")
                print("2. Зарегистрируйте новых пользователей")
                print("3. Назначьте администратора: python create_admin.py")

            except Exception as e:
                print(f"❌ Ошибка при удалении базы: {e}")
        else:
            print("❌ Операция отменена")
    else:
        print(f"ℹ️  База данных не найдена: {db_path}")
        print("   Создаю новую базу...")

        try:
            from app.database import engine, Base
            from app.models import User, Like, Match, Message

            Base.metadata.create_all(bind=engine)
            print("✅ База данных создана успешно")

        except Exception as e:
            print(f"❌ Ошибка при создании базы: {e}")


def show_database_stats():
    """Показать статистику базы данных"""
    db_path = "./itmatch.db"

    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("📊 Статистика базы данных:")
        print("-" * 40)

        tables = ["users", "likes", "matches", "messages"]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize():12} : {count}")

        print("-" * 40)

        # Дополнительная информация
        cursor.execute("SELECT username, email, is_admin FROM users LIMIT 5")
        users = cursor.fetchall()

        if users:
            print("\n👥 Первые пользователи:")
            for user in users:
                admin_flag = "👑" if user[2] else ""
                print(f"  {admin_flag} {user[0]} ({user[1]})")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка при чтении базы: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Утилиты для работы с базой данных ITmatch")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nИспользование:")
        print("  python reset_db.py reset    - очистить базу данных")
        print("  python reset_db.py stats    - показать статистику")
        print("\n⚠️  ВНИМАНИЕ: 'reset' удалит ВСЕ данные!")
    else:
        command = sys.argv[1]

        if command == "reset":
            reset_database()
        elif command == "stats":
            show_database_stats()
        else:
            print(f"❌ Неизвестная команда: {command}")