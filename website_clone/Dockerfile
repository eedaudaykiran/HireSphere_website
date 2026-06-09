# ── Base image ─────────────────────────────────────────────
# Use official Python 3.11 slim image (smaller size)
FROM python:3.11-slim

# ── Set environment variables ───────────────────────────────
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# ── Set working directory inside container ──────────────────
# All commands run from this folder inside container
WORKDIR /app

# ── Install system dependencies ─────────────────────────────
# psycopg2 needs these to connect to PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies ─────────────────────────────
# Copy requirements first (Docker caches this layer)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ── Copy project files into container ───────────────────────
COPY . .

# ── Collect static files ────────────────────────────────────
RUN python manage.py collectstatic --noinput

# ── Expose port 8000 ────────────────────────────────────────
EXPOSE 8000

# ── Run Django development server ───────────────────────────
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]