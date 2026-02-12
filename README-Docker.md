# Badminton Club Management - Docker Setup

🐳 รันแอพทั้งหมดด้วย Docker Compose

## Quick Start

```bash
# 1. Clone หรือเข้าไปที่ project directory
cd ~/.openclaw/workspace/projects/badminton_app

# 2. Copy environment file
cp .env.example .env

# 3. แก้ไข .env - ใส่ LINE Login credentials
nano .env

# 4. Start all services
docker-compose up --build

# 5. เปิด browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js 14 + React |
| Backend | 8000 | FastAPI + Python 3.13 |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache + Sessions |

## LINE Login Setup (Required)

1. ไปที่ https://developers.line.biz/
2. Login ด้วย LINE account
3. สร้าง Provider: `Badminton Club`
4. สร้าง Channel (เลือก "LINE Login")
5. ตั้งค่า:
   - App types: Web app
   - Callback URL: `http://localhost:3000/auth/line/callback`
6. Copy `Channel ID` และ `Channel Secret` ใส่ใน `.env`

## Commands

```bash
# Start
docker-compose up

# Start in background
docker-compose up -d

# Stop
docker-compose down

# Stop and remove volumes (⚠️ ลบข้อมูลทั้งหมด)
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild
docker-compose up --build

# Run commands in container
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Data Persistence

- **PostgreSQL**: เก็บใน Docker volume `postgres_data`
- **Redis**: เก็บใน Docker volume `redis_data`

## Production Deployment

1. เปลี่ยน `SECRET_KEY` ใน `.env`
2. ตั้งค่า `LINE_REDIRECT_URI` เป็น domain จริง
3. ใช้ `docker-compose.prod.yml` (ถ้ามี)
4. ตั้งค่า SSL/HTTPS

## Troubleshooting

### Port already in use
```bash
# หา process ที่ใช้ port
lsof -i :3000
lsof -i :8000
lsof -i :5432
lsof -i :6379

# หรือเปลี่ยน port ใน docker-compose.yml
```

### Database connection error
```bash
# รอให้ database ready
docker-compose logs -f postgres

# หรือ restart
docker-compose restart backend
```

### Permission denied
```bash
# Fix permissions
sudo chown -R $USER:$USER .
```
