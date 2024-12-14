#### 
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY src/api/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY src/api/ /app

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=index.py

# Expose the port Flask will run on
EXPOSE 8000

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]

# docker build -t api .
# docker run -p 8000:8000 api