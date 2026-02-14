# Badminton Club Management App - TODO List

## วันที่อัปเดท: 14 กุมภาพันธ์ 2026

---

## ✅ เสร็จแล้ว (Done)

### Backend & Infrastructure
- [x] Setup FastAPI + SQLModel
- [x] Setup PostgreSQL database (Render Basic-1gb)
- [x] Setup Redis (Upstash)
- [x] Deploy backend on Render
- [x] LINE Login integration
- [x] Auto token refresh
- [x] OAuth state validation
- [x] FCM v1 for push notifications
- [x] Email SMTP configuration
- [x] UUID generation for models
- [x] Fix timezone issues
- [x] Make Redis optional
- [x] Fix all SQLAlchemy relationship errors

### Frontend
- [x] Deploy frontend on Render
- [x] LINE Login button
- [x] Club creation
- [x] Club list page
- [x] Session creation form
- [x] Auto-refresh expired tokens
- [x] Remove all mockup data
- [x] Change terminology "นัดตี" → "Session"
- [x] Rich club cards with details
- [x] "ก๊วนของฉัน" section on home page
- [x] Navigation improvements

### Authentication & Security
- [x] JWT token implementation
- [x] SECRET_KEY validation
- [x] Password hashing
- [x] CORS configuration
- [x] Protected routes

---

## 🔄 กำลังทำ (In Progress)

### Testing & Debugging
- [ ] Test session creation (optional end time)
- [ ] Test end-to-end user flow
- [ ] Monitor Render logs for errors
- [ ] Performance testing

---

## 🚨 Critical Security Fixes (Priority: URGENT)

จาก Audit Report - ต้องแก้ก่อนเปิดให้ใช้จริง:

- [ ] **WebSocket Authentication** - ตอนนี้ใครก็ต่อได้
- [ ] **Rate Limiting** - เพิ่ม limit ที่ auth endpoints (ป้องกัน brute-force)
- [ ] **Database Migrations** - ย้ายจาก `create_all` เป็น Alembic migrations
- [ ] **WebSocket CORS** - แก้จาก `*` เป็น domain ที่กำหนด
- [ ] **Bug refresh_token** - แก้ variable shadowing

## 🎨 UX Quick Wins (Priority: HIGH)

ตาม Audit - ขาดแค่ 3 ปุ่ม ใช้งานไม่ได้:

- [ ] **ปุ่ม "เปิดรับสมัคร"** - เปลี่ยน Session จาก DRAFT → OPEN
- [ ] **ปุ่ม "เข้าร่วมก๊วน"** - บนหน้า Club detail
- [ ] **หน้า "ค้นหาก๊วนสาธารณะ"** - ให้คนใหม่หาได้
- [ ] **แก้ Timezone Display** - แสดงเวลาถูกต้อง (ไม่มี -07:00)

## 📋 ยังไม่ได้ทำ (To Do)

### Phase 1: Core Features (Priority High)
- [ ] Join club via QR code/invite
- [ ] Club member management
- [ ] Session registration (เข้าร่วม session)
- [ ] Session check-in/check-out
- [ ] Match creation and scoring
- [ ] Payment calculation (3 types)

### Phase 2: Advanced Features (Priority Medium)
- [ ] Matchmaking system
- [ ] Pre-match arrangement
- [ ] Court management
- [ ] Auto-matching per court
- [ ] Anti-gaming detection
- [ ] Club verification system
- [ ] Ranking/leaderboard

### Phase 3: Payment & Notifications (Priority Medium)
- [ ] Payment request via Inbox
- [ ] QR code upload for payment
- [ ] Payment proof upload
- [ ] Push notification for payments
- [ ] Email notifications

### Phase 4: Polish & Optimization (Priority Low)
- [ ] Mobile app (PWA)
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Export data

### Technical Debt
- [ ] Unit tests
- [ ] Integration tests
- [ ] API documentation
- [ ] Database backup strategy
- [ ] Monitoring/alerting

---

## 🐛 Bugs ที่พบและแก้แล้ว

| Bug | สถานะ | วันที่แก้ |
|-----|--------|-----------|
| Club creation "Not Found" error | ✅ Fixed | 14/02 |
| Phantom match history | ✅ Fixed | 14/02 |
| Invalid token on login | ✅ Fixed | 14/02 |
| Network unreachable (Supabase) | ✅ Fixed (ใช้ Render PostgreSQL) | 14/02 |
| Tables not created | ✅ Fixed | 14/02 |
| 401 Unauthorized | ✅ Fixed (auto-refresh) | 14/02 |
| OAuth state validation failed | ✅ Fixed | 14/02 |
| Timezone error | ✅ Fixed | 14/02 |
| Mockup data showing | ✅ Fixed | 14/02 |

---

## 📊 สถานะปัจจุบัน

**Deployment:** ✅ Live
- Backend: https://tofubadminton-backend.onrender.com
- Frontend: https://tofubadminton-frontend.onrender.com

**ค่าใช้จ่ายต่อเดือน:**
- PostgreSQL: $19
- Backend Starter: $7
- Frontend: Free
- Redis: Free
- **รวม: $26/เดือน**

---

## 📝 Notes

- ใช้ System Design V2 เป็นแนวทางพัฒนา
- Phase 1 (Core) ใกล้เสร็จแล้ว
- ต้องทดสอบการใช้งานจริงกับผู้ใช้
- ควรมีระบบ monitor errors
