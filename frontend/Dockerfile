# ============================================================
# Frontend Dockerfile (React)
# ============================================================
# Chế độ: Development (hot-reload qua npm start)
# Để chạy Production, xem hướng dẫn bên dưới

# === DEVELOPMENT MODE (default) ===
FROM node:25-alpine

WORKDIR /app

# Copy package files trước để tận dụng Docker layer cache
COPY package*.json ./

# Cài đặt dependencies
RUN npm install

# Copy source code
COPY . .

EXPOSE 5173


CMD ["npm", "run", "dev"]

# ============================================================
# PRODUCTION MODE (uncomment khi cần deploy)
# ============================================================
#
# WARNING: CÁC ĐOẠN CODE DƯỚI ĐÂY KHÔNG CÒN ĐÚNG!
# Dự án đã thay đổi từ react-scripts sang vite, vậy nên các
# đoạn code dưới đây không còn đúng nữa! Cần cập nhật lại
#
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
