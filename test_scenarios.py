#!/usr/bin/env python3
"""
Тестирование основных сценариев ITmatch
"""
import sys
import os
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"


def print_step(step_num, description):
    """Печатает шаг тестирования"""
    print(f"\n{'=' * 60}")
    print(f"ШАГ {step_num}: {description}")
    print(f"{'=' * 60}")


def test_registration():
    """Тест регистрации пользователей"""
    print_step(1, "Регистрация тестовых пользователей")

    users = [
        {
            "username": "Админ Тестовый",
            "email": "admin@itmatch.test",
            "password": "admin123",
            "specialization": "Backend",
            "experience": "Senior",
            "bio": "Системный администратор и разработчик"
        },
        {
            "username": "Разработчик Петр",
            "email": "dev1@itmatch.test",
            "password": "dev123",
            "specialization": "Backend",
            "experience": "Middle",
            "bio": "Python разработчик с опытом 3 года"
        },
        {
            "username": "Дизайнер Анна",
            "email": "designer@itmatch.test",
            "password": "design123",
            "specialization": "Frontend",
            "experience": "Junior",
            "bio": "UI/UX дизайнер, начинающий frontend разработчик"
        },
        {
            "username": "Data Scientist Иван",
            "email": "data@itmatch.test",
            "password": "data123",
            "specialization": "Data Science",
            "experience": "Senior",
            "bio": "Специалист по машинному обучению и анализу данных"
        }
    ]

    for i, user_data in enumerate(users, 1):
        print(f"\n{i}. Регистрация: {user_data['username']}")

        # Подготавливаем данные формы
        form_data = user_data.copy()

        # Отправляем POST запрос
        response = requests.post(
            f"{BASE_URL}/register",
            data=form_data,
            allow_redirects=False
        )

        if response.status_code in [200, 302, 303]:
            print(f"   ✅ Успешно: {user_data['email']}")
        else:
            print(f"   ❌ Ошибка: статус {response.status_code}")


def test_login():
    """Тест входа пользователей"""
    print_step(2, "Вход пользователей и получение сессий")

    test_users = [
        {"email": "admin@itmatch.test", "password": "admin123"},
        {"email": "dev1@itmatch.test", "password": "dev123"}
    ]

    sessions = {}

    for user in test_users:
        print(f"\nВход: {user['email']}")

        response = requests.post(
            f"{BASE_URL}/login",
            data=user,
            allow_redirects=False
        )

        if response.status_code == 302:
            # Получаем куки из ответа
            cookies = response.cookies.get_dict()
            sessions[user['email']] = cookies

            # Проверяем профиль
            profile_response = requests.get(
                f"{BASE_URL}/profile",
                cookies=cookies
            )

            if profile_response.status_code == 200:
                print(f"   ✅ Успешный вход, сессия установлена")
                print(f"   📋 Проверка профиля: OK")
            else:
                print(f"   ⚠️  Вход успешен, но профиль недоступен")
        else:
            print(f"   ❌ Ошибка входа")

    return sessions


def test_feed_and_likes(sessions):
    """Тест ленты и системы лайков"""
    print_step(3, "Тестирование ленты и системы лайков")

    # Используем сессию разработчика
    dev_cookies = sessions.get("dev1@itmatch.test")
    if not dev_cookies:
        print("   ❌ Нет сессии разработчика")
        return

    print("\n1. Доступ к ленте:")
    response = requests.get(
        f"{BASE_URL}/feed",
        cookies=dev_cookies
    )

    if response.status_code == 200:
        print("   ✅ Лента доступна")

        # Пробуем найти других пользователей в ленте
        if "backend" in response.text.lower() or "frontend" in response.text.lower():
            print("   ✅ Пользователи отображаются в ленте")
    else:
        print(f"   ❌ Лента недоступна: статус {response.status_code}")

    # Тестируем лайки
    print("\n2. Тест системы лайков:")

    # Сначала нужно получить ID других пользователей
    # Для упрощения предположим, что есть пользователи с ID 1, 3, 4
    test_likes = [1, 3, 4]  # ID пользователей для лайков

    for user_id in test_likes:
        response = requests.post(
            f"{BASE_URL}/like/{user_id}",
            cookies=dev_cookies,
            allow_redirects=False
        )

        if response.status_code in [303, 302]:
            print(f"   ✅ Лайк пользователю {user_id} отправлен")
        else:
            print(f"   ⚠️  Лайк пользователю {user_id}: статус {response.status_code}")


def test_matches(sessions):
    """Тест системы совпадений"""
    print_step(4, "Тестирование системы совпадений")

    # Используем сессию разработчика
    dev_cookies = sessions.get("dev1@itmatch.test")
    if not dev_cookies:
        print("   ❌ Нет сессии разработчика")
        return

    print("\n1. Проверка страницы совпадений:")
    response = requests.get(
        f"{BASE_URL}/matches",
        cookies=dev_cookies
    )

    if response.status_code == 200:
        print("   ✅ Страница совпадений доступна")

        # Проверяем наличие элементов интерфейса
        if "совпадений" in response.text.lower():
            print("   ✅ Интерфейс совпадений корректный")
    else:
        print(f"   ❌ Совпадения недоступны: статус {response.status_code}")


def test_messages(sessions):
    """Тест системы сообщений"""
    print_step(5, "Тестирование системы сообщений")

    # Используем сессию разработчика
    dev_cookies = sessions.get("dev1@itmatch.test")
    if not dev_cookies:
        print("   ❌ Нет сессии разработчика")
        return

    print("\n1. Проверка списка сообщений:")
    response = requests.get(
        f"{BASE_URL}/messages",
        cookies=dev_cookies
    )

    if response.status_code in [200, 302]:
        print("   ✅ Система сообщений доступна")
    else:
        print(f"   ❌ Сообщения недоступны: статус {response.status_code}")
        return

    # Тестируем создание сообщения (если есть матч)
    print("\n2. Тест отправки сообщения:")

    # Для теста используем матч ID 1 (если он существует)
    test_match_id = 1

    response = requests.post(
        f"{BASE_URL}/messages/{test_match_id}/send",
        data={"message": "Тестовое сообщение от скрипта проверки"},
        cookies=dev_cookies,
        allow_redirects=False
    )

    if response.status_code in [303, 302]:
        print("   ✅ Отправка сообщения работает")
    elif response.status_code == 404:
        print("   ⚠️  Матч не найден (это нормально если нет совпадений)")
    else:
        print(f"   ⚠️  Отправка сообщения: статус {response.status_code}")


def test_admin_panel():
    """Тест админ-панели"""
    print_step(6, "Тестирование админ-панели")

    print("\n1. Проверка доступности админ-панели:")
    response = requests.get(f"{BASE_URL}/admin")

    if response.status_code == 200:
        print("   ✅ Админ-панель доступна")

        # Проверяем наличие формы входа
        if "login" in response.text.lower() or "вход" in response.text.lower():
            print("   ✅ Форма входа присутствует")
    else:
        print(f"   ❌ Админ-панель недоступна: статус {response.status_code}")


def test_error_pages():
    """Тест обработки ошибок"""
    print_step(7, "Тестирование обработки ошибок")

    test_urls = [
        ("/nonexistent", "Несуществующая страница"),
        ("/profile", "Профиль без авторизации"),
        ("/feed", "Лента без авторизации"),
        ("/user/9999", "Несуществующий пользователь"),
    ]

    for url, description in test_urls:
        print(f"\n{description}:")
        response = requests.get(f"{BASE_URL}{url}", allow_redirects=False)

        if response.status_code in [404, 401, 302, 403]:
            print(f"   ✅ Обработка ошибки корректна: статус {response.status_code}")
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")


def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Начинаем тестирование ITmatch")
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")

    try:
        # Проверяем доступность сервера
        print("\n🔍 Проверка доступности сервера...")
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code in [200, 307]:
            print("✅ Сервер доступен")
        else:
            print(f"❌ Сервер недоступен: статус {response.status_code}")
            return

        # Запускаем тесты
        test_registration()
        sessions = test_login()

        if sessions:
            test_feed_and_likes(sessions)
            test_matches(sessions)
            test_messages(sessions)

        test_admin_panel()
        test_error_pages()

        print(f"\n{'=' * 60}")
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"{'=' * 60}")
        print("\n📋 Рекомендации:")
        print("1. Проверьте логи сервера на наличие ошибок")
        print("2. Протестируйте UI вручную через браузер")
        print("3. Проверьте работу загрузки файлов (аватарок)")
        print("4. Убедитесь, что все ссылки работают корректно")

    except requests.ConnectionError:
        print(f"\n❌ Не удалось подключиться к серверу {BASE_URL}")
        print("   Убедитесь, что сервер запущен: python run.py")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]

    run_all_tests()