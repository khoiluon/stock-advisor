# StockAdvisor 📈

Ứng dụng tư vấn đầu tư chứng khoán tại Việt Nam.

## 🔧 Công nghệ sử dụng
- **Frontend**: ReactJS 19, TailwindCSS, Lightweight Charts, D3.js
- **Backend**: Django 5.2 (Python 3.11), Django REST Framework, Django Channels (WebSocket)
- **Database**: MySQL 8.0
- **Cache/Broker**: Redis 7
- **Task Queue**: Celery + Celery Beat
- **ASGI Server**: Daphne (hỗ trợ HTTP + WebSocket)
- **Data Sources**: SSI FastConnect, vnstock, CafeF (Firecrawl), Google Gemini AI

## ⚙️ Chức năng chính
- Vẽ biểu đồ kỹ thuật cổ phiếu (candlestick, indicators)
- Lấy dữ liệu cổ phiếu tự động từ SSI/vnstock
- Streaming dữ liệu real-time qua WebSocket
- Gợi ý thông minh cổ phiếu nên đầu tư ngắn hạn/trung hạn (AI)
- Crawl và phân tích tin tức tài chính tự động
- Lưu cổ phiếu yêu thích
- Chatbot tư vấn đầu tư (Gemini AI)

## 🚀 Quick Start (Docker — Khuyến nghị)

### Yêu cầu
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (bao gồm Docker Compose)
- API Keys: SSI FastConnect, Firecrawl, Google Gemini (xem `.env.example`)

### Bước 1: Clone repo
```bash
git clone <repo-url>
cd StockAdvisor
```

### Bước 2: Cấu hình Environment
```bash
# Backend
cp backend/.env.example backend/.env
# Mở backend/.env và điền API keys (SSI, Firecrawl, Gemini)

# Frontend  
cp frontend/.env.example frontend/.env
# Thường không cần sửa gì
```

### Bước 3: Khởi chạy
```bash
docker compose up --build
```

Lần đầu build sẽ mất ~5-10 phút (cài TA-Lib, Python/Node dependencies).

### Bước 4: Migrate Database
```bash
# Mở terminal mới, chạy:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

### Bước 5: Truy cập
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |

### Các lệnh hữu ích
```bash
# Dừng tất cả services
docker compose down

# Dừng và xoá database (reset hoàn toàn)
docker compose down -v

# Xem logs của 1 service
docker compose logs -f backend
docker compose logs -f celery_worker

# Chạy Django management commands
docker compose exec backend python manage.py <command>

# Kiểm tra Celery worker
docker compose exec celery_worker celery -A investcore inspect active

# Rebuild sau khi thay đổi requirements.txt hoặc Dockerfile
docker compose up --build
```

## 💻 Chạy Local (Không Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
# Lưu ý: Cần cài TA-Lib C library trước (xem https://ta-lib.github.io/ta-lib-python/)
# Lưu ý: Cần MySQL và Redis đang chạy trên localhost

cp .env.example .env
# Sửa .env: DB_HOST=localhost, REDIS_URL=redis://localhost:6379/0

python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm start
```

## 📦 Về package SSI FastConnect Data (`ssi_fc_data`)
File `ssi_fc_data-2.2.2.tar.gz` đã được đưa vào repo. Khi chạy Docker, nó được cài tự động qua `requirements.txt`. Khi chạy local, pip sẽ tìm file theo đường dẫn trong container — bạn có thể cài thủ công:
```bash
cd backend
pip install ssi_fc_data-2.2.2.tar.gz
```

## 🏗️ Kiến trúc Docker

```
                    ┌─────────────┐
                    │  Frontend   │ :3000
                    │  (React)    │
                    └──────┬──────┘
                           │ HTTP/WS
                    ┌──────▼──────┐
                    │   Backend   │ :8000
                    │  (Daphne)   │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              │            │            │
       ┌──────▼──┐  ┌──────▼──┐  ┌──────▼──────┐
       │  MySQL  │  │  Redis  │  │   Celery    │
       │   (DB)  │  │ (Cache) │  │  Worker +   │
       │  :3307  │  │  :6379  │  │    Beat     │
       └─────────┘  └─────────┘  └─────────────┘
```

## 📁 Cấu trúc project
```
StockAdvisor/
├── docker-compose.yml          # Cấu hình Docker (dev)
├── backend/
│   ├── Dockerfile
│   ├── .env.example            # Template biến môi trường
│   ├── requirements.txt
│   ├── ssi_fc_data-2.2.2.tar.gz  # SSI package (commit vào repo)
│   ├── manage.py
│   ├── investcore/             # Django project settings
│   ├── api/                    # App chính (models, views, tasks)
│   └── ssi_integration/        # SSI streaming & data fetching
└── frontend/
    ├── Dockerfile
    ├── .env.example
    ├── package.json
    └── src/                    # React source code
```
