# Google Cloud Run: container listens on PORT (default 8080).
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

COPY ml_pipeline ./ml_pipeline
COPY api ./api
COPY models ./models

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Cloud Run sets PORT at runtime (often 8080).
CMD ["sh", "-c", "uvicorn api.http_app:app --host 0.0.0.0 --port ${PORT:-8080}"]
