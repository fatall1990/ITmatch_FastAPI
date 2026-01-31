from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from sqlalchemy import func
from datetime import datetime, timedelta
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

    def is_visible(self, request: Request) -> bool:
        """Показывать только администраторам"""
        return request.session.get("admin", False)

    def is_accessible(self, request: Request) -> bool:
        """Доступ только администраторам"""
        return request.session.get("admin", False)

    @expose("/stats", methods=["GET"])
    async def stats_page(self, request: Request):
        """Страница со статистикой"""
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

            # Создаем простой шаблон для статистики
            html_content = self._generate_stats_html(
                total_users=total_users,
                active_users=active_users,
                admin_users=admin_users,
                total_likes=total_likes,
                total_matches=total_matches,
                total_messages=total_messages,
                new_users_week=new_users_week,
                new_likes_week=new_likes_week,
                new_matches_week=new_matches_week,
                specializations=specializations_list,
                experiences=experiences_list
            )

            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)

        finally:
            db.close()

    def _generate_stats_html(self, **kwargs):
        """Генерирует HTML для страницы статистики"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Статистика - ITmatch Admin</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
            <style>
                body {{ padding: 20px; background-color: #f8f9fa; }}
                .stat-card {{ transition: transform 0.2s; border-radius: 10px; }}
                .stat-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
                .stat-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
                .stat-number {{ font-size: 2.2rem; font-weight: bold; }}
                .stat-label {{ color: #6c757d; font-size: 0.9rem; }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="row mb-4">
                    <div class="col-12">
                        <h1><i class="bi bi-graph-up me-2"></i>Статистика ITmatch</h1>
                        <p class="text-muted">Общая статистика платформы</p>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-xl-3 col-md-6 mb-3">
                        <div class="card stat-card border-primary">
                            <div class="card-body text-center py-4">
                                <i class="bi bi-people-fill stat-icon text-primary"></i>
                                <div class="stat-number">{kwargs['total_users']}</div>
                                <div class="stat-label">Всего пользователей</div>
                                <div class="stat-change text-success">
                                    <small>+{kwargs['new_users_week']} за неделю</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-3">
                        <div class="card stat-card border-success">
                            <div class="card-body text-center py-4">
                                <i class="bi bi-heart-fill stat-icon text-success"></i>
                                <div class="stat-number">{kwargs['total_likes']}</div>
                                <div class="stat-label">Всего лайков</div>
                                <div class="stat-change text-success">
                                    <small>+{kwargs['new_likes_week']} за неделю</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-3">
                        <div class="card stat-card border-info">
                            <div class="card-body text-center py-4">
                                <i class="bi bi-people stat-icon text-info"></i>
                                <div class="stat-number">{kwargs['total_matches']}</div>
                                <div class="stat-label">Всего совпадений</div>
                                <div class="stat-change text-success">
                                    <small>+{kwargs['new_matches_week']} за неделю</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-3">
                        <div class="card stat-card border-warning">
                            <div class="card-body text-center py-4">
                                <i class="bi bi-chat-dots-fill stat-icon text-warning"></i>
                                <div class="stat-number">{kwargs['total_messages']}</div>
                                <div class="stat-label">Всего сообщений</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0"><i class="bi bi-person-badge me-2"></i>Статистика пользователей</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm">
                                    <tr>
                                        <td>Активные пользователи</td>
                                        <td class="text-end"><span class="badge bg-success">{kwargs['active_users']}</span></td>
                                    </tr>
                                    <tr>
                                        <td>Администраторы</td>
                                        <td class="text-end"><span class="badge bg-primary">{kwargs['admin_users']}</span></td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header bg-success text-white">
                                <h5 class="mb-0"><i class="bi bi-pie-chart me-2"></i>Распределение по специализациям</h5>
                            </div>
                            <div class="card-body">
        """

        if kwargs['specializations']:
            html += '<ul class="list-group list-group-flush">'
            for spec, count in kwargs['specializations']:
                html += f'''
                <li class="list-group-item d-flex justify-content-between">
                    <span>{spec}</span>
                    <span class="badge bg-secondary">{count}</span>
                </li>
                '''
            html += '</ul>'
        else:
            html += '<p class="text-muted">Нет данных</p>'

        html += '''
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header bg-info text-white">
                                <h5 class="mb-0"><i class="bi bi-bar-chart me-2"></i>Распределение по опыту</h5>
                            </div>
                            <div class="card-body">
        '''

        if kwargs['experiences']:
            html += '<ul class="list-group list-group-flush">'
            for exp, count in kwargs['experiences']:
                html += f'''
                <li class="list-group-item d-flex justify-content-between">
                    <span>{exp}</span>
                    <span class="badge bg-info">{count}</span>
                </li>
                '''
            html += '</ul>'
        else:
            html += '<p class="text-muted">Нет данных</p>'

        html += f'''
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header bg-secondary text-white">
                                <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>Информация</h5>
                            </div>
                            <div class="card-body">
                                <p class="small text-muted">
                                    <i class="bi bi-clock"></i> Данные обновляются в реальном времени
                                </p>
                                <p class="small text-muted">
                                    <i class="bi bi-calendar-week"></i> Статистика за неделю: последние 7 дней
                                </p>
                                <a href="/admin" class="btn btn-outline-primary btn-sm">
                                    <i class="bi bi-arrow-left"></i> Назад в админку
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="text-center text-muted small">
                            <hr>
                            <p>
                                <i class="bi bi-cpu"></i> ITmatch Admin Panel • 
                                <i class="bi bi-clock-history"></i> Обновлено: {datetime.now().strftime("%d.%m.%Y %H:%M")}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''

        return html


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