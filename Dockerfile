# Stage 1: Builder stage to install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation tools for dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install packages from requirements.txt to user directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final lightweight runner image
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend files
COPY database.py models.py auth.py main.py ai_tutor.py ./

# Copy static frontend index.html inside the frontend folder
COPY frontend/ ./frontend/

# Expose port for FastAPI backend
EXPOSE 8000

# Set environment variables for stdout/stderr flushing
ENV PYTHONUNBUFFERED=1

# Command to run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
