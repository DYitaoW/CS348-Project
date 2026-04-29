# Backend container for Google Cloud Run
# - Uses gunicorn (production WSGI server)
# - Listens on $PORT (Cloud Run sets this)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT} wsgi:app"]
