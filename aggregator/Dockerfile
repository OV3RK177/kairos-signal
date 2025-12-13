FROM python:3.10-slim

# 1. Setup Environment
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# 2. Install Dependencies (Layered for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install Code
COPY . .

# 4. The Entrypoint
# We run python directly.
CMD ["python", "cortex_engine.py"]
