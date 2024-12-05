# Use an official Node.js image as the base image
FROM node:18-alpine

# Set the working directory to /app/src/frontend inside the container
WORKDIR /app/src/frontend

# Copy package.json and package-lock.json
COPY src/frontend/package.json src/frontend/package-lock.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the frontend application code
COPY src/frontend ./

# Build the Next.js app for production
RUN npm run build

# Expose the port that Next.js will run on
EXPOSE 3000

# Command to run the application in production
CMD ["npm", "start"]
