# Use a Node.js base image
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the app files
COPY . .

# Expose the development server port
EXPOSE 5173

# Start the Vite dev server
CMD ["npm", "run", "dev", "--", "--host"]
