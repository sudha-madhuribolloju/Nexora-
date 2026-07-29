# ==========================================================
# NEXORA AI Classroom Portal - React + Vite Frontend Dockerfile
# Multi-stage build supporting Development & Production
# ==========================================================

# ----------------------------------------------------------
# Stage 1: Base Node 20 Environment
# ----------------------------------------------------------
FROM node:20-alpine AS base

WORKDIR /app

# Install curl/wget for healthchecks
RUN apk add --no-cache wget curl

# Copy package manifests first for caching layer
COPY package.json package-lock.json* ./

# ----------------------------------------------------------
# Stage 2: Development Stage (Live reload target)
# ----------------------------------------------------------
FROM base AS development

ENV NODE_ENV=development

# Install dependencies (including devDependencies)
RUN npm ci || npm install

# Copy application source code
COPY . .

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Development server command with external host access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# ----------------------------------------------------------
# Stage 3: Build Stage for Production Static Assets
# ----------------------------------------------------------
FROM base AS builder

ENV NODE_ENV=production

RUN npm ci || npm install

COPY . .

# Build Vite static distribution bundle
RUN npm run build

# ----------------------------------------------------------
# Stage 4: Production Stage (Nginx Static File Server)
# ----------------------------------------------------------
FROM nginx:1.25-alpine AS production

# Remove default static pages
RUN rm -rf /usr/share/nginx/html/*

# Copy built frontend assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
