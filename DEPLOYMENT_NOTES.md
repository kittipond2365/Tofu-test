# Badminton App - Change Log & Notes

## วันที่ 14 กุมภาพันธ์ 2026

### โครงสร้างระบบ
- **Backend:** FastAPI + SQLModel + PostgreSQL (Supabase)
- **Frontend:** Next.js 14 + TypeScript + Tailwind
- **Database:** Supabase PostgreSQL (Free tier)
- **Cache/Realtime:** Upstash Redis (Free tier)
- **Deployment:** Render (Web Service + Static Site)

### Environment Variables (Render)
```
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
REDIS_URL=rediss://default:[token]@xxx.upstash.io:6379
SECRET_KEY=[random-64-chars]
LINE_CHANNEL_ID=[from-line-console]
LINE_CHANNEL_SECRET=[from-line-console]
FIREBASE_PROJECT_ID=[optional]
FCM_SERVICE_ACCOUNT_JSON=[optional]
```

### ปัญหากำลังแก้
- [ ] Backend "Network unreachable" - ตรวจสอบ Redis/Database connection
- [ ] ถอด Redis ออกชั่วคราวเพื่อเทส (วิธีที่ 2)

### สิ่งที่เสร็จแล้ว
- [x] SQLite test ผ่านทุก feature (User, Club, Session, Match)
- [x] Production cleanup (ลบ test files, SQLite code)
- [x] Frontend TypeScript fix (SessionStatus missing properties)
- [x] Setup Supabase PostgreSQL
- [x] Setup Upstash Redis
- [x] Commit: `dd3aa22` - Production cleanup

### คำสั่งสำคัญ
```bash
# Deploy บน Render
Render Dashboard → Manual Deploy → Deploy latest commit

# Check logs
Render Dashboard → Service → Logs

# Test local (ถ้าจำเป็น)
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

### หมายเหตุ
- ใช้ PostgreSQL อย่างเดียว (ไม่มี SQLite ใน production)
- Redis ใช้ Upstash (rediss:// คือ SSL)
- Frontend + Backend deploy แยกกัน
- ต้องมี SECRET_KEY ยาว 32+ ตัว
