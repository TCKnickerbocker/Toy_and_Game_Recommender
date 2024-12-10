# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY src/models/model_4/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# RUN pip install -r requirements.txt

COPY /src/models/model_4/ .

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1


# Expose the port Flask will run on
EXPOSE 5006

# Run the Flask app
CMD ["python", "call_model_4.py"]


# docker build -t model_4 .
# docker run -p 5006:5006 model_4
