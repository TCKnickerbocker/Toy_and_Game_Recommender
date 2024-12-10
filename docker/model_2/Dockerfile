# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY src/models/model_2/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# RUN pip install -r requirements.txt

COPY /src/models/model_2/ .

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1


# Expose the port Flask will run on
EXPOSE 5004

# Run the Flask app
CMD ["python", "call_model_2.py"]


# docker build -t model_2 .
# docker run -p 5004:5004 model_2
