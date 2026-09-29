FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn>=0.34.0" \
    "google-adk>=0.4.0" \
    "a2a-sdk[http-server]>=1.0.0,<2" \
    "google-cloud-aiplatform==1.165.1" \
    "google-genai>=1.0.0" \
    "google-cloud-firestore>=2.19.0" \
    "google-cloud-storage>=2.18.0" \
    "pillow>=10.4.0" \
    "pydantic>=2.10.0" \
    "python-multipart>=0.0.12" \
    "httpx>=0.28.0"

COPY . .

EXPOSE 8080

CMD ["python3", "-m", "uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
