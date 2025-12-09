FROM python:3.11-slim

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY python_backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for database persistence
RUN mkdir -p /app/data

# Set environment variable for database to use the data volume
# This ensures the DB is stored in the volume mount point
ENV DATABASE_URL="sqlite:////app/data/backroom_parlor.db"

# Command to run the bot
CMD ["python", "python_backend/main.py"]
