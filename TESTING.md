# Инструкция по тестированию ITmatch

## Подготовка к тестированию

### 1. Запуск сервера
```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Запустите сервер
python run.py