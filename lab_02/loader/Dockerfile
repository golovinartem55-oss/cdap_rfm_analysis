# Базовый образ
FROM python:3.10-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser

# Копирование и установка зависимостей
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Финальный образ
FROM python:3.10-slim

# Копирование установленных пакетов
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Создание пользователя
RUN useradd -m -u 1000 appuser

# Рабочая директория
WORKDIR /app

# Копирование скрипта
COPY loader.py .
RUN chown -R appuser:appuser /app

# Переключение на пользователя
USER appuser

# Команда запуска
CMD ["python", "loader.py"]
