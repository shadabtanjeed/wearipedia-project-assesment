# Build stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy all other source code
COPY . .

# Hard-code the API URL - pointing to our backend container
RUN echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Build the application
RUN npm run build

# Runtime stage with Nginx
FROM nginx:alpine

# Copy built assets from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check to ensure nginx is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]