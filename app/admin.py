from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from .database import engine, SessionLocal
from .models import User, Like, Match, Message
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Важно: используем ТОТ ЖЕ контекст, что и в users.py
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

                # ПРОВЕРЯЕМ ЯВЛЯЕТСЯ ЛИ ПОЛЬЗОВАТЕЛЬ АДМИНОМ
                if not user.is_admin:
                    logger.warning(f"⚠️  Пользователь {user.email} не является администратором")
                    return False

                logger.info(f"✅ Найден пользователь-админ: {user.email}")
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


# Админ-классы с расширенным функционалом
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.specialization,
        User.experience,
        User.is_active,
        User.is_admin,
        User.created_at
    ]
    column_searchable_list = [User.username, User.email]
    column_filters = [
        User.specialization,
        User.experience,
        User.is_active,
        User.is_admin
    ]
    column_sortable_list = [User.created_at, User.id]
    form_columns = [
        "username",
        "email",
        "specialization",
        "experience",
        "bio",
        "is_active",
        "is_admin"
    ]

    # Действия в списке пользователей
    column_formatters = {
        User.is_active: lambda m, a: "✅" if m.is_active else "❌",
        User.is_admin: lambda m, a: "👑" if m.is_admin else ""
    }

    # Русские названия
    column_labels = {
        "id": "ID",
        "username": "Имя",
        "email": "Email",
        "specialization": "Специализация",
        "experience": "Опыт",
        "is_active": "Активен",
        "is_admin": "Админ",
        "created_at": "Дата регистрации",
        "bio": "О себе"
    }


class LikeAdmin(ModelView, model=Like):
    column_list = [Like.id, Like.from_user_id, Like.to_user_id, Like.created_at]
    column_sortable_list = [Like.created_at, Like.id]
    column_labels = {
        "id": "ID",
        "from_user_id": "От пользователя",
        "to_user_id": "К пользователю",
        "created_at": "Дата лайка"
    }


class MatchAdmin(ModelView, model=Match):
    column_list = [Match.id, Match.user1_id, Match.user2_id, Match.created_at]
    column_sortable_list = [Match.created_at, Match.id]
    column_labels = {
        "id": "ID",
        "user1_id": "Пользователь 1",
        "user2_id": "Пользователь 2",
        "created_at": "Дата создания"
    }


class MessageAdmin(ModelView, model=Message):
    column_list = [
        Message.id,
        Message.match_id,
        Message.sender_id,
        Message.text,
        Message.created_at,
        Message.is_read
    ]
    column_searchable_list = [Message.text]
    column_filters = [Message.is_read]
    column_sortable_list = [Message.created_at, Message.id]

    # Форматирование для лучшего отображения
    column_formatters = {
        Message.text: lambda m, a: m.text[:50] + "..." if len(m.text) > 50 else m.text,
        Message.is_read: lambda m, a: "✅" if m.is_read else "📧"
    }

    column_labels = {
        "id": "ID",
        "match_id": "ID совпадения",
        "sender_id": "Отправитель",
        "text": "Текст",
        "created_at": "Дата отправки",
        "is_read": "Прочитано"
    }


class StatsView(BaseView):
    """Страница статистики для админ-панели"""

    name = "📊 Статистика"
    icon = "fa-solid fa-chart-bar"

    @expose("/stats", methods=["GET"])
    def stats_page(self, request: Request):
        """Страница со статистикой"""
        from sqlalchemy import func
        from datetime import datetime, timedelta

        db = SessionLocal()

        try:
            # Основная статистика
            total_users = db.query(func.count(User.id)).scalar() or 0
            active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
            admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0

            total_likes = db.query(func.count(Like.id)).scalar() or 0
            total_matches = db.query(func.count(Match.id)).scalar() or 0
            total_messages = db.query(func.count(Message.id)).scalar() or 0

            # Статистика за последние 7 дней
            week_ago = datetime.utcnow() - timedelta(days=7)

            new_users_week = db.query(func.count(User.id)).filter(
                User.created_at >= week_ago
            ).scalar() or 0

            new_likes_week = db.query(func.count(Like.id)).filter(
                Like.created_at >= week_ago
            ).scalar() or 0

            new_matches_week = db.query(func.count(Match.id)).filter(
                Match.created_at >= week_ago
            ).scalar() or 0

            # Статистика по специализациям
            specializations = db.query(
                User.specialization,
                func.count(User.id).label('count')
            ).group_by(User.specialization).all()

            # Статистика по опыту
            experiences = db.query(
                User.experience,
                func.count(User.id).label('count')
            ).group_by(User.experience).all()

            # Подготовка данных для шаблона
            specializations_list = [(s[0], s[1]) for s in specializations]
            experiences_list = [(e[0], e[1]) for e in experiences]

            context = {
                "request": request,
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "total_likes": total_likes,
                "total_matches": total_matches,
                "total_messages": total_messages,
                "new_users_week": new_users_week,
                "new_likes_week": new_likes_week,
                "new_matches_week": new_matches_week,
                "specializations": specializations_list,
                "experiences": experiences_list,
            }

            return self.templates.TemplateResponse(
                "admin/stats.html",
                context
            )

        finally:
            db.close()


# Обновляем функцию setup_admin
def setup_admin(app):
    """Настройка админ-панели"""
    from sqladmin import templates

    authentication_backend = AdminAuth(
        secret_key="your-secret-key-here-change-in-production"
    )

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="ITmatch Admin Panel",
        base_url="/admin",
        logo_url="/static/admin-logo.png",
    )

    # Регистрируем модели и страницы
    admin.add_view(UserAdmin)
    admin.add_view(LikeAdmin)
    admin.add_view(MatchAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(StatsView)  # <-- ДОБАВЛЯЕМ СТРАНИЦУ СТАТИСТИКИ

    logger.info("✅ Админ-панель настроена (с аутентификацией и статистикой)")
    return admin