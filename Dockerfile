# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /api

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the API port
EXPOSE 8000

# Start the API
CMD ["python3", "api/index.py"]