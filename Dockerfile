# 1) Этап сборки (build stage).
FROM python:3.13-slim AS build

# Устанавливаем build-tools для компиляции (gcc и deps для aiokafka).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем uv из официального образа.
COPY --from=ghcr.io/astral-sh/uv:0.8.21 /uv /uvx /bin/

WORKDIR /app

# Оптимизации uv.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Синхронизируем зависимости.
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev --frozen

# Добавляем код и финализируем (только src для минимального размера).
COPY src/ /app/src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 2) Этап запуска (runtime stage).
FROM python:3.13-slim AS runtime

# PATH для .venv.
ENV PATH="/app/.venv/bin:$PATH"

# PYTHONPATH для src-layout.
ENV PYTHONPATH=/app/src

WORKDIR /app

# Non-root user.
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /telegram_boto -s /bin/false appuser

# Копируем приложение (только src и .venv).
COPY --from=build --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=build --chown=appuser:appgroup /app/src /app/src

USER appuser

# Запуск (с префиксом для src).
CMD ["python", "-m", "telegram_bot.main"]