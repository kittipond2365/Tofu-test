# 🚀 Deployment Guide - Badminton Club App

**Deploy แบบ Vercel (Frontend) + Render (Backend)** - แนะนำที่สุด

---

## 📋 สิ่งที่ต้องเตรียม

### 1. LINE Login Credentials
- ไปที่ https://developers.line.biz/
- สร้าง Channel หรือใช้ที่มีอยู่
- เอา **Channel ID** และ **Channel Secret**
- กำหนด Callback URL (ใส่ภายหลัง)

### 2. VAPID Keys (สำหรับ Web Push)
```bash
# Generate VAPID keys
npm install -g web-push
web-push generate-vapid-keys

# จะได้:
# Public Key:  <ใส่ตรงนี้>
# Private Key: <ใส่ตรงนี้>
```

### 3. SMTP Email (Gmail)
- ใช้ Gmail Account
- สร้าง App Password: https://myaccount.google.com/apppasswords
- เอา email และ app password

---

## 🔧 ขั้นตอนการ Deploy

### Step 1: Deploy Backend บน Render

#### 1.1 สร้าง Web Service
1. ไปที่ https://dashboard.render.com/
2. กด **New +** → **Web Service**
3. Connect GitHub repo: `tofubadminton`
4. ตั้งค่า:
   - **Name**: `badminton-backend`
   - **Root Directory**: `backend`
   - **Runtime**: **Docker**
   - **Branch**: `main`

#### 1.2 Environment Variables
ไปที่ tab **Environment** ใส่:

```bash
# Database (จาก PostgreSQL ที่สร้างไว้)
DATABASE_URL=postgresql://<your-db-url>
DATABASE_URL_SYNC=postgresql://<your-db-url>

# Security
SECRET_KEY=<สร้างด้วยคำสั่ง openssl rand -hex 32>
ENVIRONMENT=production
DEBUG=false

# CORS (ใส่หลัง deploy frontend)
CORS_ORIGINS_STR=https://<your-frontend-url>.vercel.app

# LINE OAuth
LINE_CHANNEL_ID=<your-line-channel-id>
LINE_CHANNEL_SECRET=<your-line-channel-secret>
LINE_REDIRECT_URI=https://<your-frontend-url>.vercel.app/auth/line/callback

# Email SMTP
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-gmail>@gmail.com
SMTP_PASSWORD=<your-app-password>
SMTP_FROM_EMAIL=<your-gmail>@gmail.com

# Web Push (VAPID)
WEB_PUSH_ENABLED=true
WEB_PUSH_VAPID_PUBLIC_KEY=<your-vapid-public-key>
WEB_PUSH_VAPID_PRIVATE_KEY=<your-vapid-private-key>
WEB_PUSH_VAPID_CLAIMS_EMAIL=<your-email>@gmail.com

# Redis (optional)
REDIS_URL=redis://<your-redis-url>
```

#### 1.3 Deploy
- กด **Create Web Service**
- รอ 3-5 นาที
- จะได้ URL: `https://badminton-backend-XXXX.onrender.com`
- **จด URL นี้ไว้** ใช้ในขั้นตอนหน้า

---

### Step 2: Deploy Frontend บน Vercel

#### 2.1 สร้าง Project
1. ไปที่ https://vercel.com/
2. Login ด้วย GitHub
3. กด **Add New Project**
4. Import repo: `tofubadminton`

#### 2.2 ตั้งค่า
- **Framework**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

#### 2.3 Environment Variables
กด **Environment Variables** ใส่:

```bash
NEXT_PUBLIC_API_URL=https://<backend-url>/api/v1
NEXT_PUBLIC_WEB_PUSH_VAPID_PUBLIC_KEY=<your-vapid-public-key>
NODE_ENV=production
```

#### 2.4 Deploy
- กด **Deploy**
- รอ 1-2 นาที
- จะได้ URL: `https://badminton-frontend-XXXX.vercel.app`
- **จด URL นี้ไว้**

---

### Step 3: อัปเดต Configuration

#### 3.1 อัปเดต CORS บน Render
ไปที่ Render Dashboard → badminton-backend → Environment:
```
CORS_ORIGINS_STR=https://<vercel-frontend-url>
```

#### 3.2 อัปเดต LINE Callback
ไปที่ https://developers.line.biz/:
1. เข้า Channel → LINE Login → Callback settings
2. เพิ่ม URL:
```
https://<vercel-frontend-url>/auth/line/callback
```

#### 3.3 อัปเดต LINE_REDIRECT_URI บน Render
```
LINE_REDIRECT_URI=https://<vercel-frontend-url>/auth/line/callback
```

---

### Step 4: ทดสอบ

1. เปิด Frontend URL (Vercel)
2. กด "เข้าสู่ระบบด้วย LINE"
3. ควร redirect ไป LINE → ยืนยัน → กลับมา login สำเร็จ!

---

## 💰 ค่าใช้จ่าย

| Service | Platform | ราคา/เดือน |
|---------|----------|------------|
| Frontend | **Vercel** | **ฟรี** |
| Backend | Render | $7-15 |
| Database | Render | มีอยู่แล้ว |
| **รวม** | | **~$7-15** |

---

## 🔧 คำสั่งที่ใช้บ่อย

### Generate Secret Key
```bash
openssl rand -hex 32
```

### Generate VAPID Keys
```bash
npx web-push generate-vapid-keys
```

### Test Health Endpoint
```bash
curl https://<backend-url>/health
```

---

## 🆘 Troubleshooting

### CORS Error
- ตรวจสอบ `CORS_ORIGINS_STR` ต้องตรงกับ Frontend URL
- ไม่มี trailing slash
- ต้องมี `https://`

### LINE OAuth ไม่ผ่าน
- ตรวจสอบ `LINE_REDIRECT_URI` ใช้ HTTPS
- Callback URL ใน LINE Console ต้องตรงกัน
- State parameter ต้องผ่าน Redis

### Database Connection Failed
- ตรวจสอบ `DATABASE_URL` format
- PostgreSQL ต้องเปิด SSL ใน production

---

## 📝 หมายเหตุสำคัญ

- **อย่า commit secrets ลง GitHub**
- ใช้ Render/Vercel Environment Variables เท่านั้น
- เก็บ secrets ไว้ที่เครื่องหรือ password manager

---

*อัปเดตล่าสุด: 2025-02-12*
