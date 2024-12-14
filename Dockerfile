## Test model 1 via 
# docker build -t model_1 .
# docker run -p 5003:5003 model_1
# curl http://localhost:5003/most_similar_products

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first (to leverage caching)
COPY src/models/model_1/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY src/models/model_1/ ./

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the Flask application port
EXPOSE 5003

# Run the Flask application
CMD ["python", "call_model_1.py"]
