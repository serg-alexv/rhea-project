# Rhea FastAPI Backend — Production Image
FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by some Python packages (e.g. libzmq for pyzmq)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY opera/ ./opera/
COPY prompts/ ./prompts/
COPY friends/ ./friends/

# Optional: copy rhea-nexus profiles (used by rhea_profile_manager.py at runtime)
# These are loaded lazily, so the app starts fine without them.
# COPY rhea-nexus/ ./rhea-nexus/

# Ensure all internal modules are importable
ENV PYTHONPATH="/app/src:/app/friends/ruliad/explorer:/app"

# Create writable directories the app needs at runtime
RUN mkdir -p /app/logs /app/data

EXPOSE 8000

CMD ["python3", "src/rhead.py"]
