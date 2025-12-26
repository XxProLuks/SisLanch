# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY ./backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage - minimal image
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./backend /app/backend
COPY ./database /app/database

#Create logs directory
RUN mkdir -p /app/logs

# Set working directory to backend
WORKDIR /app/backend

# Create non-root user for security
RUN useradd -m -u 1000 lanch && chown -R lanch:lanch /app
USER lanch

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

