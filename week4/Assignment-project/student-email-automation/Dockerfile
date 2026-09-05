# ==============================================================================
# Dockerfile for Student Email Automation Dashboard
# Compatible with Render, Railway, Hugging Face Spaces, Fly.io, or Docker Cloud
# ==============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure data, templates, and logs directories exist
RUN mkdir -p data templates logs static

# Expose default port
EXPOSE 8000

# Start Uvicorn web server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
