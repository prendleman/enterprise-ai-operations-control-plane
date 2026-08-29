FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AI_PROVIDER=mock \
    DATABASE_URL=sqlite:///./data/ai_ops.db \
    CONFIG_DIR=/app/config

COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY config ./config
COPY scripts ./scripts
COPY dashboard ./dashboard

RUN pip install --no-cache-dir -e . \
    && mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
