# Dockerfile for Railway deployment
FROM python:3.11-slim

# Install Node.js (needed for frontend build)
# First install curl and other dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source and build
# Copy all frontend files at once
COPY frontend_source/ ./frontend_source/
WORKDIR /app/frontend_source
# Install dependencies and build
RUN npm install
RUN npm run build

# Copy built frontend to static directory
WORKDIR /app
RUN mkdir -p static && cp -r frontend_source/dist/* static/

# Copy the rest of the application
COPY . .

# Expose port (Railway sets PORT env var)
ENV PORT=8000
EXPOSE $PORT

# Start the application
CMD python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
