# ============================================================
# Backend Dockerfile (Django + Daphne + Celery)
# ============================================================
# Hỗ trợ: Django, Channels (WebSocket), Celery, TA-Lib, SSI FCData
# Server: Daphne (ASGI) — hỗ trợ cả HTTP và WebSocket

FROM python:3.11-slim

# --- Biến môi trường tối ưu cho Python trong Docker ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Cài đặt system dependencies ---
# build-essential, pkg-config: tools để build C extensions
# default-libmysqlclient-dev: cho mysqlclient (MySQL driver)
# wget: tải TA-Lib source
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        wget \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Cài đặt TA-Lib C Library (yêu cầu bởi TA-Lib Python) ---
RUN wget -q https://github.com/TA-Lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
    tar -xzf ta-lib-0.6.4-src.tar.gz && \
    cd ta-lib-0.6.4 && \
    ./configure --prefix=/usr && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf ta-lib-0.6.4 ta-lib-0.6.4-src.tar.gz

# --- Thư mục làm việc ---
WORKDIR /app

# --- Copy file SSI FCData trước (cần cho pip install) ---
# File này phải được commit vào Git repo
COPY ssi_fc_data-2.2.2.tar.gz /app/ssi_fc_data-2.2.2.tar.gz

# --- Cài đặt Python dependencies ---
# Copy requirements trước để tận dụng Docker layer cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy toàn bộ source code ---
COPY . /app/

# --- Cấu hình entrypoint script ---
# Script này đợi MySQL sẵn sàng + chạy migrations trước khi start service
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# --- Mở port ---
EXPOSE 8000

# --- Entrypoint: đợi DB + migrate ---
ENTRYPOINT ["/app/entrypoint.sh"]

# --- Lệnh mặc định: chạy Daphne ASGI server ---
# Hỗ trợ cả HTTP requests và WebSocket connections
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "investcore.asgi:application"]