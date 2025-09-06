FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    jq \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Make local path dependency available during install (exported as -e path)
COPY libs/synesthetic-schemas/python libs/synesthetic-schemas/python
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest
RUN pip install pytest

COPY . .

# Create test directory with proper permissions
RUN mkdir -p /app/tests/data && \
    chmod -R 777 /app/tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
