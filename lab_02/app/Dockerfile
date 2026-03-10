# Базовый образ
FROM python:3.10-slim AS builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN useradd -m -u 1000 appuser

# Копирование и установка зависимостей
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# Финальный образ
FROM python:3.10-slim

# Создание пользователя
RUN useradd -m -u 1000 appuser

# Копирование установленных пакетов
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Настройка прав
RUN chown -R appuser:appuser /home/appuser

# Рабочая директория
WORKDIR /app

# Копирование кода приложения
COPY --chown=appuser:appuser app.py .

# Переключение на пользователя
USER appuser

# Добавление локальных бинарников в PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Healthcheck (будет переопределен в docker-compose)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Команда запуска
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
