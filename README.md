# 🏸 Badminton Club Management App

ระบบจัดการชมรมแบดมินตัน พร้อม LINE Login และระบบแข่งขันอัตโนมัติ

## ✨ Features

- 🔐 **LINE Login** - เข้าสู่ระบบด้วย LINE อย่างเดียว
- 👥 **Club Management** - จัดการชมรม เชิญสมาชิก
- 📅 **Session Management** - สร้างกิจกรรม เปิดรับสมัคร
- 🏸 **Auto Matchmaking** - จับคู่แข่งขันอัตโนมัติตามระดับ
- 📊 **Statistics & Charts** - กราฟสถิติ Recharts
- 🔔 **Notifications** - Email + Push Notification
- 📱 **Mobile Responsive** - ใช้งานบนมือถือได้เต็มรูปแบบ

## 🛠️ Tech Stack

### Backend
- FastAPI + Python 3.13
- PostgreSQL 16
- Redis 7
- Socket.IO (Real-time)
- JWT Authentication

### Frontend
- Next.js 14 + TypeScript
- Tailwind CSS
- React Query (TanStack)
- Zustand (State Management)
- Recharts (Charts)
- Lucide React (Icons)

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/pondai/tofubadminton.git
cd tofubadminton
cp .env.example .env
```

### 2. Configure Environment
แก้ไข `.env`:
```bash
LINE_CHANNEL_ID=your-channel-id
LINE_CHANNEL_SECRET=your-channel-secret
SECRET_KEY=your-secret-key
```

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Access
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
tofubadminton/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── api/         # API Routes
│   │   ├── core/        # Config, Security
│   │   ├── models/      # Database Models
│   │   ├── schemas/     # Pydantic Schemas
│   │   └── services/    # Business Logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Next.js Frontend
│   ├── src/
│   │   ├── app/        # Pages
│   │   ├── components/ # React Components
│   │   ├── lib/        # Utils, API
│   │   └── stores/     # Zustand Stores
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # Development
├── docker-compose.prod.yml  # Production
└── README.md
```

## 🔧 Configuration

### LINE Login Setup
1. ไปที่ https://developers.line.biz/
2. สร้าง Provider + Channel (LINE Login)
3. ตั้งค่า Callback URL: `http://localhost:3000/auth/line/callback`
4. คัดลอก Channel ID และ Secret ใส่ใน `.env`

### Email SMTP (Optional)
```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### FCM Push (Optional)
```bash
FCM_ENABLED=true
FCM_SERVER_KEY=your-fcm-key
```

## 🧪 Testing

```bash
# Run tests
~/.openclaw/scripts/test-badminton-auto.sh
```

## 📱 Screenshots

*(เพิ่ม screenshots ตามจริง)*

## 🚀 Deployment

### Deploy to Railway/Render
1. Push code ขึ้น GitHub
2. เชื่อม Railway/Render กับ GitHub repo
3. ตั้งค่า Environment Variables
4. Deploy!

## 📝 License

MIT License

## 👨‍💻 Developer

Pond + Taohoo (OpenClaw Agent)
