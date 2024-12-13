# # Use an official Node.js image as the base image
# FROM node:18-alpine

# # Set the working directory to /app inside the container
# WORKDIR /app

# # Install global dependencies
# RUN npm install -g npm@latest

# # Copy only package.json and package-lock.json first
# COPY src/frontend/package*.json ./

# # Clear any existing node_modules and install dependencies
# RUN rm -rf node_modules && npm install --legacy-peer-deps

# # Copy the rest of the frontend application code
# COPY src/frontend ./

# # Expose the port that the app will run on
# EXPOSE 4000

# # For development
# CMD ["npm", "run", "start"]

# Use an official Node.js image as the base image
FROM node:18-alpine

# Set the working directory to /app inside the container
WORKDIR /app

# Install global dependencies
RUN npm install -g npm@latest

# Copy package.json and package-lock.json
COPY src/frontend/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Install react-scripts globally
RUN npm install -g react-scripts

# Copy the rest of the frontend application code
COPY src/frontend ./

# Expose the port that the app will run on
EXPOSE 4000

# For development
CMD ["npm", "run", "start"]
