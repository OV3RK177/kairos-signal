# Base image: Lightweight Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Default command (will be overridden in docker-compose)
CMD ["python3"]
