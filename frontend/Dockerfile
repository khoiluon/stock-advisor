# ============================================================
# Frontend Dockerfile (React)
# ============================================================
# Chế độ: Development (hot-reload qua npm start)
# Để chạy Production, xem hướng dẫn bên dưới

# === DEVELOPMENT MODE (default) ===
FROM node:18-alpine

WORKDIR /app

# Copy package files trước để tận dụng Docker layer cache
COPY package*.json ./

# Cài đặt dependencies
RUN npm install

# Copy source code
COPY . .

EXPOSE 3000

# Biến môi trường cho hot-reload trong Docker
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

CMD ["npm", "start"]

# ============================================================
# PRODUCTION MODE (uncomment khi cần deploy)
# ============================================================
# Sử dụng multi-stage build: build React → serve bằng Nginx
#
# --- Stage 1: Build ---
# FROM node:18-alpine AS builder
# WORKDIR /app
# COPY package*.json ./
# RUN npm ci --only=production
# COPY . .
# RUN npm run build
#
# --- Stage 2: Serve ---
# FROM nginx:alpine
# COPY --from=builder /app/build /usr/share/nginx/html
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]