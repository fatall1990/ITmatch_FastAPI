// Простой скрипт для обновления чата (без WebSocket)
function refreshChat() {
    if (window.location.pathname.startsWith('/messages/')) {
        setTimeout(function() {
            window.location.reload();
        }, 30000); // Обновлять каждые 30 секунд
    }
}

// Запускаем при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    refreshChat();
});