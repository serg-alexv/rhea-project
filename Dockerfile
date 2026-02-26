# Rhea Tribunal API — Docker Container
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and necessary modules
COPY src/ ./src/
COPY opera/ ./opera/
COPY prompts/ ./prompts/
COPY docs/ ./docs/
COPY config/ ./config/
COPY friends/ ./friends/

# Set environment variables
ENV PYTHONPATH="/app/src:/app/friends/ruliad/explorer:/app"
ENV TRIBUNAL_PORT=8080

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run the API
CMD ["uvicorn", "src.tribunal_api:app", "--host", "0.0.0.0", "--port", "8080"]
