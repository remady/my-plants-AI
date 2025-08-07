FROM python:3.13.2-slim

# Create non-root user early
RUN useradd -m appuser

# Set working directory and switch to non-root user
WORKDIR /app
RUN chown appuser:appuser /app
USER appuser

# Set non-sensitive environment variables
ARG APP_ENV=production
ARG POSTGRES_URL

ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POSTGRES_URL=${POSTGRES_URL}

# Install system dependencies as root (needed for apt-get)
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && pip install --upgrade pip \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# Switch back to appuser
USER appuser

# Copy pyproject.toml first (Docker cache optimization)
COPY --chown=appuser:appuser pyproject.toml .

# Install Python dependencies into local venv
RUN uv venv && . .venv/bin/activate && uv pip install -e .

# Copy the rest of the application with correct ownership
COPY --chown=appuser:appuser . .

# Make entrypoint script executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Create log directory
RUN mkdir -p /app/logs

# Expose default port
EXPOSE 8000

# Log the environment we're using
RUN echo "Using ${APP_ENV} environment"

# Command to run the application
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]