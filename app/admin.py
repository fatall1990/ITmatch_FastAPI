# app/admin.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (используем тот же контекст, что и в users.py)
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from .database import engine, SessionLocal
from .models import User, Like, Match, Message
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Важно: используем ТОТ ЖЕ контекст, что и в users.py
# users.py: pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt", "django_pbkdf2_sha256"], deprecated="auto")
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt", "django_pbkdf2_sha256"], deprecated="auto")


class AdminAuth(AuthenticationBackend):
    """Аутентификация для админ-панели"""

    async def login(self, request: Request) -> bool:
        """Обработка входа в админку"""
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

            logger.info(f"🔐 Попытка входа: username={username}")

            if not username or not password:
                logger.warning("❌ Пустые данные")
                return False

            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == username).first()

                if not user:
                    logger.warning(f"❌ Пользователь {username} не найден")
                    return False

                logger.info(f"✅ Найден пользователь: {user.email}")
                logger.info(f"   Хэш в БД: {user.hashed_password}")

                # ВАЖНО: Используем verify без указания схемы, контекст сам определит
                try:
                    is_valid = pwd_context.verify(password, user.hashed_password)
                    logger.info(f"   Результат проверки: {is_valid}")

                    if is_valid:
                        logger.info(f"✅ Правильный пароль для {user.email}")

                        # Устанавливаем сессию
                        request.session.update({
                            "admin": True,
                            "user_id": user.id,
                            "email": user.email
                        })

                        logger.info(f"✅ Сессия установлена")
                        return True
                    else:
                        logger.warning(f"❌ Неверный пароль для {user.email}")
                        return False

                except Exception as verify_error:
                    logger.error(f"🔥 Ошибка при проверке пароля: {verify_error}")
                    return False

            finally:
                db.close()

        except Exception as e:
            logger.error(f"🔥 Общая ошибка: {e}", exc_info=True)
            return False

    async def logout(self, request: Request) -> bool:
        """Выход из админки"""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Проверка аутентификации"""
        is_admin = request.session.get("admin", False)
        logger.info(f"🔍 Проверка аутентификации. Admin: {is_admin}")
        return is_admin


# Админ-классы
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.specialization, User.experience]
    column_searchable_list = [User.username, User.email]
    column_filters = [User.specialization, User.experience]


class LikeAdmin(ModelView, model=Like):
    column_list = [Like.id, Like.from_user_id, Like.to_user_id, Like.created_at]


class MatchAdmin(ModelView, model=Match):
    column_list = [Match.id, Match.user1_id, Match.user2_id, Match.created_at]


class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.sender_id, Message.text, Message.created_at, Message.is_read]


def setup_admin(app):
    """Настройка админ-панели"""
    authentication_backend = AdminAuth(
        secret_key="your-secret-key-here-change-in-production"
    )

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="ITmatch Admin",
        base_url="/admin"
    )

    admin.add_view(UserAdmin)
    admin.add_view(LikeAdmin)
    admin.add_view(MatchAdmin)
    admin.add_view(MessageAdmin)

    logger.info("✅ Админ-панель настроена")
    return admin
# Функция для настройки админки
def setup_admin(app):
    """Настройка админ-панели"""

    # Важно: используем тот же secret_key, что и в SessionMiddleware
    authentication_backend = AdminAuth(
        secret_key="your-secret-key-here-change-in-production"  # ТОТ ЖЕ КЛЮЧ ЧТО В main.py
    )

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="ITmatch Admin",
        base_url="/admin"
    )

    # Регистрируем модели
    admin.add_view(UserAdmin)
    admin.add_view(LikeAdmin)
    admin.add_view(MatchAdmin)
    admin.add_view(MessageAdmin)

    logger.info("✅ Админ-панель настроена (с аутентификацией)")
    return admin