# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:24-alpine AS build-stage

WORKDIR /app

# Copy package files for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Create directory for extra nginx configs
RUN mkdir -p /etc/nginx/extra-conf.d

# Copy nginx configuration files
COPY ./nginx/index.conf /etc/nginx/conf.d/default.conf
COPY ./nginx/nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf


# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
