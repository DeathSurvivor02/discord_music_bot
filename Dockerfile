FROM python:3.11-slim

# Install system dependencies (ffmpeg is essential for yt-dlp audio extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000

# Start FastAPI audio engine
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
