# ==============================================================================
# Stage 1: Build the frontend static assets with Node.js
# ==============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies based on lockfile
COPY Frontend/package.json Frontend/package-lock.json ./
RUN npm ci

# Copy the frontend application source code
COPY Frontend/ ./

# Build production bundle and generate static entry (output to .output/public)
RUN npm run build

# ==============================================================================
# Stage 2: Build the Python backend image and include frontend static files
# ==============================================================================
FROM python:3.11-slim

# Install uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    STATIC_DIR=/app/static \
    HOST=0.0.0.0 \
    PORT=8000 \
    PATH="/app/.venv/bin:$PATH"

# Copy dependency configuration files first for layer caching
COPY Backend/pyproject.toml Backend/uv.lock /app/

# Install backend dependencies with uv into virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source code
COPY Backend/ /app/

# Install the backend package
RUN uv sync --frozen --no-dev

# Copy built frontend static files from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/.output/public /app/static

EXPOSE 8000

# Start the application server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
