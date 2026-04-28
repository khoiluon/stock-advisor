# ============================================================
# Nginx Dockerfile — Multi-stage Build
# ============================================================
# Stage 1: Build React app bằng Node.js + NPM
# Stage 2: Serve React static files bằng Nginx
#
# Kiến trúc: Frontend KHÔNG chạy container riêng.
# Nginx vừa serve React static files, vừa reverse proxy đến Backend.
# ============================================================

# --- Stage 1: Build React App ---
FROM node:25-alpine AS builder

WORKDIR /app

# Build arguments: URL API và WebSocket (inject lúc docker build)
# Giá trị mặc định cho local build, sẽ được override bởi docker-compose
ARG VITE_API_URL=http://localhost/api
ARG VITE_WS_URL=ws://localhost/ws
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Copy package files trước (tận dụng Docker layer cache)
# Chỉ thay đổi layer npm install khi package.json thay đổi
COPY frontend/package*.json ./

# Copy local libs (cần cho file: protocol trong package.json)
# Phải copy TRƯỚC npm install vì package.json reference file:./libs/...
COPY frontend/libs/ ./libs/

# Cài đặt dependencies bằng NPM
RUN npm install --ignore-scripts

# Copy toàn bộ source code frontend
COPY frontend/ .

RUN rm -f .env .env.local .env.production .env.development

# Build production bundle
RUN npm run build

# --- Stage 2: Nginx serve React + reverse proxy ---
FROM nginx:1.27-alpine

# Xóa config mặc định của Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copy React build output từ Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx config custom
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
