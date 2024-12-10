# # Base image
# FROM python:3.9-slim

# # Set working directory
# WORKDIR /api

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application code
# COPY . .

# # Expose the API port
# EXPOSE 8000

# # Start the API
# CMD ["python3", "api/index.py"]

# # Use an official Node.js image as the base image
# FROM node:18-alpine

# # Set the working directory to /app/src/frontend inside the container
# WORKDIR /app/src/frontend

# # Copy package.json and package-lock.json
# COPY src/frontend/package.json src/frontend/package-lock.json ./

# # Install dependencies
# RUN npm install --production --legacy-peer-deps  # Owen's works without these flags
# # RUN npm install --production


# # Copy the rest of the frontend application code
# COPY src/frontend ./

# # Build the Next.js app for production
# RUN npm run build

# # Expose the port that Next.js will run on
# EXPOSE 3000

# # Command to run the application in production
# CMD ["npm", "start"]


# # docker build -t frontend .
# # docker run -p 3000:3000 frontend



###

# # Use an official Python runtime as a parent image
# FROM python:3.9-slim

# # Set the working directory in the container
# WORKDIR /app

# # Copy the current directory contents into the container
# COPY src/models/generate_new_products/requirements.txt ./

# # Install dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt
# # RUN pip install -r requirements.txt

# COPY /src/models/generate_new_products/ .

# # Set environment variables from .env file
# ENV PYTHONUNBUFFERED=1


# # Expose the port Flask will run on
# EXPOSE 5007

# # Run the Flask app
# CMD ["python", "call_generate_model.py"]

# docker build -t generate_new_products .
# docker run -p 5007:5007 generate_new_products


###

# # Use an official Python runtime as a parent image
# FROM python:3.9-slim

# # Set the working directory in the container
# WORKDIR /app

# # Copy the requirements.txt into the container
# COPY src/models/model_1/requirements.txt ./

# # Install dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# # Copy .env file into the container
# COPY .env /app

# # Set environment variables from .env file
# ENV PYTHONUNBUFFERED=1

# # Copy the rest of the application code into the container
# COPY src/models/model_1/ .

# # Expose the port Flask will run on
# EXPOSE 5003

# # Run the Flask app
# CMD ["python", "call_model_1.py"]
# # docker build -t model_1 .
# # docker run -p 5003:5003 model_1

# #### 
# # Use an official Python runtime as a parent image
# FROM python:3.9-slim

# # Set the working directory in the container
# WORKDIR /app

# # Copy the current directory contents into the container
# COPY src/api/requirements.txt ./

# # Install dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt


# COPY src/api/ /app

# # Set environment variables from .env file
# ENV PYTHONUNBUFFERED=1
# ENV FLASK_APP=index.py

# # Expose the port Flask will run on
# EXPOSE 8000

# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]

# # docker build -t api .
# # docker run -p 8000:8000 api
