# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src .

# Expose the API port
EXPOSE 5000

# Start the API
CMD ["python", "api/inference_api.py"]
