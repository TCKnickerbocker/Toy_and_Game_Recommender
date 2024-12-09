# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY src/models/generate_new_products/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# RUN pip install -r requirements.txt

COPY /src/models/generate_new_products/ .

# Set environment variables from .env file
ENV PYTHONUNBUFFERED=1


# Expose the port Flask will run on
EXPOSE 5004

# Run the Flask app
CMD ["python", "call_generate_model.py"]

# docker build -t generate_new_products .
# docker run -p 5004:5004 generate_new_products
