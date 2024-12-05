# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# RUN pip install -r requirements.txt

# Copy .env file to the container
COPY .env /app

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1

# Expose the port Flask will run on
EXPOSE 5003

# Run the Flask app
CMD ["python", "call_model_1.py"]
