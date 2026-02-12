# Frontend Dockerfile - Next.js 14
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application
COPY . .

# Build (for production)
# RUN npm run build

# Expose port
EXPOSE 3000

# Run development server
CMD ["npm", "run", "dev"]
