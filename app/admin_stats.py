"""
Дополнительные страницы статистики для админ-панели
"""
from sqladmin import BaseView, expose
from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, Like, Match, Message
from fastapi import Request
from datetime import datetime, timedelta


class StatsView(BaseView):
    """Страница статистики"""

    name = "📊 Статистика"
    icon = "fa-solid fa-chart-bar"

    @expose("/stats", methods=["GET"])
    def stats_page(self, request: Request):
        """Страница со статистикой"""
        db = SessionLocal()

        try:
            # Основная статистика
            total_users = db.query(func.count(User.id)).scalar()
            active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
            admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()

            total_likes = db.query(func.count(Like.id)).scalar()
            total_matches = db.query(func.count(Match.id)).scalar()
            total_messages = db.query(func.count(Message.id)).scalar()

            # Статистика за последние 7 дней
            week_ago = datetime.utcnow() - timedelta(days=7)

            new_users_week = db.query(func.count(User.id)).filter(
                User.created_at >= week_ago
            ).scalar()

            new_likes_week = db.query(func.count(Like.id)).filter(
                Like.created_at >= week_ago
            ).scalar()

            new_matches_week = db.query(func.count(Match.id)).filter(
                Match.created_at >= week_ago
            ).scalar()

            # Статистика по специализациям
            specializations = db.query(
                User.specialization,
                func.count(User.id)
            ).group_by(User.specialization).all()

            # Статистика по опыту
            experiences = db.query(
                User.experience,
                func.count(User.id)
            ).group_by(User.experience).all()

            context = {
                "request": request,
                "total_users": total_users or 0,
                "active_users": active_users or 0,
                "admin_users": admin_users or 0,
                "total_likes": total_likes or 0,
                "total_matches": total_matches or 0,
                "total_messages": total_messages or 0,
                "new_users_week": new_users_week or 0,
                "new_likes_week": new_likes_week or 0,
                "new_matches_week": new_matches_week or 0,
                "specializations": specializations or [],
                "experiences": experiences or [],
            }

            return self.templates.TemplateResponse(
                "admin_stats.html",
                context
            )

        finally:
            db.close()


# HTML шаблон для статистики
STATS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Статистика - ITmatch Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; }
        .stat-card { transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-icon { font-size: 2.5rem; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <h1 class="mb-4"><i class="bi bi-graph-up"></i> Статистика ITmatch</h1>

        <!-- Основные метрики -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card stat-card border-primary">
                    <div class="card-body text-center">
                        <i class="bi bi-people-fill stat-icon text-primary"></i>
                        <h2 class="mt-2">{{ total_users }}</h2>
                        <h6 class="text-muted">Всего пользователей</h6>
                        <small class="text-success">+{{ new_users_week }} за неделю</small>
                    </div>
                </div>
            </div>

            <div class="col-md-3 mb-3">
                <div class="card stat-card border-success">
                    <div class="card-body text-center">
                        <i class="bi bi-heart-fill stat-icon text-success"></i>
                        <h2 class="mt-2">{{ total_likes }}</h2>
                        <h6 class="text-muted">Всего лайков</h6>
                        <small class="text-success">+{{ new_likes_week }} за неделю</small>
                    </div>
                </div>
            </div>

            <div class="col-md-3 mb-3">
                <div class="card stat-card border-info">
                    <div class="card-body text-center">
                        <i class="bi bi-people stat-icon text-info"></i>
                        <h2 class="mt-2">{{ total_matches }}</h2>
                        <h6 class="text-muted">Всего совпадений</h6>
                        <small class="text-success">+{{ new_matches_week }} за неделю</small>
                    </div>
                </div>
            </div>

            <div class="col-md-3 mb-3">
                <div class="card stat-card border-warning">
                    <div class="card-body text-center">
                        <i class="bi bi-chat-dots-fill stat-icon text-warning"></i>
                        <h2 class="mt-2">{{ total_messages }}</h2>
                        <h6 class="text-muted">Всего сообщений</h6>
                    </div>
                </div>
            </div>
        </div>

        <!-- Дополнительная статистика -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-person-badge"></i> Статистика пользователей</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr>
                                <td>Активные пользователи</td>
                                <td class="text-end"><span class="badge bg-success">{{ active_users }}</span></td>
                            </tr>
                            <tr>
                                <td>Администраторы</td>
                                <td class="text-end"><span class="badge bg-primary">{{ admin_users }}</span></td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-pie-chart"></i> Распределение по специализациям</h5>
                    </div>
                    <div class="card-body">
                        {% if specializations %}
                            <ul class="list-group list-group-flush">
                                {% for spec, count in specializations %}
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>{{ spec }}</span>
                                    <span class="badge bg-secondary">{{ count }}</span>
                                </li>
                                {% endfor %}
                            </ul>
                        {% else %}
                            <p class="text-muted">Нет данных</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-bar-chart"></i> Распределение по опыту</h5>
                    </div>
                    <div class="card-body">
                        {% if experiences %}
                            <ul class="list-group list-group-flush">
                                {% for exp, count in experiences %}
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>{{ exp }}</span>
                                    <span class="badge bg-info">{{ count }}</span>
                                </li>
                                {% endfor %}
                            </ul>
                        {% else %}
                            <p class="text-muted">Нет данных</p>
                        {% endif %}
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-info-circle"></i> Информация</h5>
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
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Создаём файл с шаблоном
import os

os.makedirs("app/templates/admin", exist_ok=True)
with open("app/templates/admin/stats.html", "w", encoding="utf-8") as f:
    f.write(STATS_TEMPLATE)