# Badminton App System Design Report V2

> Generated: 2026-02-13 | Status: Design Document (No Implementation Code)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Bug Analysis](#1-bug-analysis)
3. [Admin System](#2-admin-system)
4. [Matchmaking System](#3-matchmaking-system)
5. [Privacy System](#4-privacy-system)
6. [Logo Upload](#5-logo-upload)
7. [Anti-Gaming](#6-anti-gaming)
8. [Render Disk Integration](#7-render-disk-integration)
9. [Implementation Priority](#implementation-priority)

---

## Executive Summary

This document covers bug analysis for two critical issues, plus system design for six new features: admin roles, matchmaking/pair requests, club privacy, logo upload, anti-gaming, and Render disk integration. Each section includes database schema, API design, and implementation guidance.

---

## 1. Bug Analysis

### Bug #1: Club Creation — "Not Found" Error

**Symptoms:** User creates club → API returns 200 → club count increases → "Club not found" error → no clubs in list.

#### Root Cause Analysis

**The bug is a missing `await db.commit()` in the create_club endpoint, combined with the session lifecycle.**

Here's what happens step-by-step:

1. **`create_club`** in `backend/app/api/clubs.py` calls `db.flush()` (line ~38, ~46) — this sends the INSERT to the database but does NOT commit the transaction.
2. The endpoint returns the `new_club` object (which has an `id` because flush assigns it).
3. **`get_db()`** in `backend/app/core/database.py` has `await session.commit()` in the `try` block after `yield`. This SHOULD commit... **but the response has already been serialized and returned to the client at `yield` time.**
4. The frontend receives the club with a valid `id`, then immediately navigates to `/clubs/${c.id}` (line ~53 in `create/page.tsx`).
5. The frontend then calls `GET /clubs/{club_id}` which opens a **new database session**. At this point, the commit from the first session may not have completed yet — **race condition**.
6. Even if the commit succeeds, the `GET /clubs/{club_id}` endpoint first checks `ClubMember` (membership check), and the `ClubMember` row was also only flushed, not committed in the same race window.

**Additionally:** The `create_club` endpoint returns `status_code=201` but the `ClubResponse` model is returned directly from the SQLModel object. If `expire_on_commit=False` is set (it is), the object stays usable, but the data may not be persisted yet.

**Secondary issue:** Cache invalidation (`cache_delete_pattern("clubs:*")`) runs BEFORE the transaction commits (it's called during `flush`, not after `commit`). So the cache is cleared, but the new data isn't in the DB yet when the next request hits.

#### Fix Strategy

| Step | File | Change | Complexity |
|------|------|--------|------------|
| 1 | `backend/app/api/clubs.py` | Add explicit `await db.commit()` after creating club + member, THEN invalidate cache | Easy |
| 2 | `backend/app/api/clubs.py` | Add `await db.refresh(new_club)` after commit to ensure all fields are loaded | Easy |
| 3 | `frontend/src/app/clubs/create/page.tsx` | Add small delay or await `queryClient.invalidateQueries` before navigation | Easy |

**Root cause summary:** Race condition between `db.flush()` (not committed) → response returned → frontend navigates → new session can't find uncommitted data.

---

### Bug #2: Phantom Match History

**Symptoms:** New user (never played) sees match history graph with matches played > 0.

#### Root Cause Analysis

**The data is hardcoded mock data in the frontend profile page.**

In `frontend/src/app/profile/page.tsx` (lines ~88-105):

```
const ratingHistory = [
  { date: 'ม.ค.', rating: 1000, matches: 5 },
  { date: 'ก.พ.', rating: 1025, matches: 8 },
  { date: 'มี.ค.', rating: 1010, matches: 6 },
  ...
];

const matchesPerMonth = [
  { month: 'ม.ค.', matches: 8 },
  { month: 'ก.พ.', matches: 12 },
  ...
];
```

These arrays are **hardcoded mock data** — NOT fetched from the API. They're always displayed regardless of whether the user has any real match history. The charts (`RatingTrendChart`, `MatchesPerMonthChart`) render this mock data for every user.

The `stats` API response (`GET /users/{user_id}/stats`) returns correct data (`total_matches`, `wins`, `losses`), but the **chart data is never fetched from the backend** — no such API endpoint exists for historical monthly breakdowns.

#### Fix Strategy

| Step | File | Change | Complexity |
|------|------|--------|------------|
| 1 | `frontend/src/app/profile/page.tsx` | Remove hardcoded mock arrays | Easy |
| 2 | `backend/app/api/stats.py` | Add `GET /users/{user_id}/match-history` endpoint that returns monthly match counts | Medium |
| 3 | `frontend/src/app/profile/page.tsx` | Fetch real data from new endpoint; show empty state when no matches | Medium |

**Root cause summary:** Frontend displays hardcoded mock chart data instead of real API data. No backend endpoint exists for monthly match history.

---

## 2. Admin System

### 2.1 Database Schema

**New/Modified Tables:**

```
# Modify UserRole enum
class UserRole(str, PyEnum):
    SUPER_ADMIN = "super_admin"   # NEW — system-wide
    OWNER = "owner"               # NEW — club creator
    ADMIN = "admin"               # existing
    ORGANIZER = "organizer"       # existing
    MEMBER = "member"             # existing

# New table: SuperAdmin (system-level)
class SuperAdmin(SQLModel, table=True):
    __tablename__ = "super_admins"
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True)
    granted_by: Optional[str] = Field(foreign_key="users.id")
    granted_at: datetime

# Modify ClubMember — add is_creator flag
class ClubMember:
    ...existing fields...
    is_creator: bool = Field(default=False)  # NEW — immutable creator flag
```

**Files to modify:**
- `backend/app/models/models.py` — Add `SuperAdmin` model, update `UserRole` enum, add `is_creator` to `ClubMember`
- `backend/app/api/clubs.py` — Set `is_creator=True` for club creator

### 2.2 Permission Matrix

| Action | Super Admin | Owner (Creator) | Admin | Organizer | Member |
|--------|:-----------:|:---------------:|:-----:|:---------:|:------:|
| Delete any club | ✅ | ❌ | ❌ | ❌ | ❌ |
| Reset any club | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign club owners | ✅ | ❌ | ❌ | ❌ | ❌ |
| Delete own club | ✅ | ✅ | ❌ | ❌ | ❌ |
| Edit club settings | ✅ | ✅ | ✅ | ❌ | ❌ |
| Appoint admins | ✅ | ✅ | ❌ | ❌ | ❌ |
| Remove admins | ✅ | ✅ | ❌ | ❌ | ❌ |
| Remove owner | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create sessions | ✅ | ✅ | ✅ | ✅ | ❌ |
| Manage courts/matches | ✅ | ✅ | ✅ | ✅ | ❌ |
| Manage registrations | ✅ | ✅ | ✅ | ✅ | ❌ |
| View club | ✅ | ✅ | ✅ | ✅ | ✅ |
| Join session | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2.3 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/admin/clubs/{club_id}/reset` | Hard reset club data | Super Admin |
| DELETE | `/admin/clubs/{club_id}` | Delete any club | Super Admin |
| POST | `/admin/clubs/{club_id}/owner` | Assign/transfer ownership | Super Admin |
| POST | `/clubs/{club_id}/admins` | Appoint admin | Owner |
| DELETE | `/clubs/{club_id}/admins/{user_id}` | Remove admin | Owner |
| PATCH | `/clubs/{club_id}/members/{user_id}/role` | Change member role | Owner/Admin |
| DELETE | `/clubs/{club_id}` | Delete club | Owner |

**Files to create/modify:**
- `backend/app/api/admin.py` — NEW: super admin endpoints
- `backend/app/api/clubs.py` — Add role management endpoints
- `backend/app/core/permissions.py` — NEW: permission checking utility
- `backend/app/main.py` — Register admin router

### 2.4 Frontend UI Components

| Component | Location | Description |
|-----------|----------|-------------|
| `AdminPanel` | `frontend/src/components/features/AdminPanel.tsx` | Super admin dashboard |
| `MemberRoleManager` | `frontend/src/components/features/MemberRoleManager.tsx` | Role assignment UI |
| `ClubSettingsPage` | `frontend/src/app/clubs/[clubId]/settings/page.tsx` | Club management page |
| Role badge | `frontend/src/components/ui/badge.tsx` | Visual role indicators |

### 2.5 Implementation Steps

1. Add `OWNER` to `UserRole` enum + migration (Easy)
2. Add `is_creator` to `ClubMember` + migration (Easy)
3. Create `SuperAdmin` table + migration (Easy)
4. Create `permissions.py` utility (Medium)
5. Update `create_club` to set `is_creator=True` and `role=OWNER` (Easy)
6. Add role management API endpoints (Medium)
7. Add super admin API endpoints (Medium)
8. Build frontend settings page (Medium)
9. Add role badges throughout UI (Easy)

**Total complexity: Medium**

---

## 3. Matchmaking System

### 3.1 Pair Request State Machine

```
[No Relationship]
       │
       ▼ (Player A sends request)
   [PENDING] ──────────────────┐
       │                        │
       ▼ (Player B accepts)     ▼ (Player B rejects / expires)
   [ACCEPTED]              [REJECTED]
       │                        │
       ▼ (Either player cancels)▼ (Can re-request after cooldown)
   [CANCELLED]            [No Relationship]
```

### 3.2 Database Schema

```
class PairRequest(SQLModel, table=True):
    __tablename__ = "pair_requests"
    __table_args__ = (
        UniqueConstraint('requester_id', 'target_id', 'club_id', name='uq_pair_request'),
    )

    id: str = Field(primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    requester_id: str = Field(foreign_key="users.id")
    target_id: str = Field(foreign_key="users.id")
    status: PairStatus  # PENDING, ACCEPTED, REJECTED, CANCELLED
    message: Optional[str]  # Optional request message
    created_at: datetime
    responded_at: Optional[datetime]
    expires_at: datetime  # Auto-expire after 7 days

class ActivePair(SQLModel, table=True):
    __tablename__ = "active_pairs"
    __table_args__ = (
        UniqueConstraint('player_a_id', 'player_b_id', 'club_id', name='uq_active_pair'),
    )

    id: str = Field(primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    player_a_id: str = Field(foreign_key="users.id")  # always lower UUID
    player_b_id: str = Field(foreign_key="users.id")  # always higher UUID
    created_from_request_id: str = Field(foreign_key="pair_requests.id")
    is_active: bool = Field(default=True)
    created_at: datetime
```

**Files to create:**
- `backend/app/models/models.py` — Add `PairRequest`, `ActivePair` models
- `backend/app/api/pairs.py` — NEW
- `backend/app/services/matchmaking.py` — Update with pair-aware logic

### 3.3 API Flow

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/clubs/{club_id}/pairs/request` | Send pair request (body: `{target_id, message?}`) |
| GET | `/clubs/{club_id}/pairs/requests` | List my pending requests (sent + received) |
| POST | `/clubs/{club_id}/pairs/requests/{id}/accept` | Accept request |
| POST | `/clubs/{club_id}/pairs/requests/{id}/reject` | Reject request |
| GET | `/clubs/{club_id}/pairs` | List my active pairs |
| DELETE | `/clubs/{club_id}/pairs/{pair_id}` | Dissolve pair |

### 3.4 Match Generation Logic (Auto-Pairing)

When generating matches for a session:

1. Get all registered players for the session
2. Query `active_pairs` for pairs where BOTH players are registered
3. **Priority pairing:** Place paired players on the same team first
4. **Remaining players:** Use existing rating-based matchmaking for unpaired players
5. **Balance check:** Ensure paired teams aren't unfairly stacked (combined rating check)

```
Algorithm: generate_matches(session_id)
  1. players = get_registered_players(session_id)
  2. pairs = get_active_pairs_where_both_in(players)
  3. paired_teams = []
  4. for each pair:
       if both players in available_pool:
         paired_teams.append((pair.player_a, pair.player_b))
         remove both from available_pool
  5. remaining = available_pool
  6. Create matches: paired_team vs paired_team (or vs random pair from remaining)
  7. Handle remaining singles with rating-based pairing
```

### 3.5 Edge Cases

| Case | Handling |
|------|----------|
| One paired player absent | Other player goes to regular matchmaking pool |
| Both absent | Skip, no match generated |
| Player late (joins mid-session) | Add to next round; if pair partner waiting, pair them |
| Player in multiple pairs | Allow — system picks best match based on who's available |
| Pair request to non-member | Reject with error: "Player must be in the same club" |
| Request to already-paired player | Allow — players can have multiple pair partners |
| Self-request | Reject |
| Request expires (7 days) | Auto-set to REJECTED, cleanup via cron/background task |

**Complexity: Hard**

---

## 4. Privacy System

### 4.1 Database Schema Changes

```
# Modify Club model — add fields:
class Club(SQLModel, table=True):
    ...existing fields...
    is_public: bool = Field(default=False)        # EXISTING
    join_password_hash: Optional[str] = Field(default=None)  # NEW — bcrypt hash
    invite_code: Optional[str] = Field(default=None, unique=True)  # NEW — for QR
    invite_code_expires_at: Optional[datetime] = Field(default=None)  # NEW
```

**File:** `backend/app/models/models.py`

### 4.2 Password Storage

- Hash with **bcrypt** (same as user passwords)
- Store in `join_password_hash` column
- Owner sets password via `PATCH /clubs/{club_id}` with `join_password` field
- Backend hashes before storing; raw password never persisted
- File: `backend/app/core/security.py` — reuse existing `hash_password` / `verify_password`

### 4.3 QR Code Generation & Validation Flow

```
Generate:
  1. Owner calls POST /clubs/{club_id}/invite-code
  2. Backend generates random invite_code (e.g., nanoid, 12 chars)
  3. Sets expiry (configurable, default 7 days)
  4. Returns invite_code
  5. Frontend generates QR containing URL: https://app.example.com/clubs/join?code={invite_code}

Scan & Join:
  1. User scans QR → opens /clubs/join?code=xxx
  2. Frontend calls POST /clubs/join-by-code with {code: xxx}
  3. Backend validates: code exists, not expired, club has capacity
  4. Creates ClubMember record
  5. Returns club info
```

### 4.4 Search/Filter Logic

```
# Public club search endpoint
GET /clubs/search?q=keyword&page=1&limit=20

Query:
  SELECT * FROM clubs
  WHERE is_public = true
  AND (name ILIKE '%keyword%' OR description ILIKE '%keyword%' OR location ILIKE '%keyword%')
  ORDER BY created_at DESC

# Private clubs: NEVER returned in search results
# Only accessible via direct invite code or password
```

### 4.5 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clubs/search` | Search public clubs (no auth required) |
| POST | `/clubs/{club_id}/join` | Join public club (existing, keep as-is) |
| POST | `/clubs/{club_id}/join-by-password` | Join private club with password |
| POST | `/clubs/join-by-code` | Join via invite code (from QR) |
| POST | `/clubs/{club_id}/invite-code` | Generate invite code (Owner/Admin) |
| DELETE | `/clubs/{club_id}/invite-code` | Revoke invite code |
| PATCH | `/clubs/{club_id}` | Update privacy settings (is_public, join_password) |

**Files to modify:**
- `backend/app/api/clubs.py` — Add join-by-password, join-by-code, invite-code endpoints
- `backend/app/schemas/schemas.py` — Add request/response schemas
- `frontend/src/app/clubs/join/page.tsx` — Add password input + QR scanner UI

**Complexity: Medium**

---

## 5. Logo Upload

### 5.1 File Storage Structure

```
/var/data/uploads/          # Render disk mount point
  clubs/
    {club_id}/
      logo.webp             # Processed logo (always webp, 256x256)
      logo_original.{ext}   # Original upload (kept for re-processing)
```

### 5.2 API Endpoint Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/clubs/{club_id}/logo` | Upload logo (multipart/form-data) |
| DELETE | `/clubs/{club_id}/logo` | Remove logo |
| GET | `/uploads/clubs/{club_id}/logo.webp` | Serve logo (static file) |

**Upload flow:**
1. Frontend sends `POST /clubs/{club_id}/logo` with `file` field
2. Backend validates: size ≤ 2MB, format in (jpg, png, webp), user is admin/owner
3. Process image: resize to 256×256, convert to webp (using Pillow)
4. Save to disk at `/var/data/uploads/clubs/{club_id}/logo.webp`
5. Update `Club.logo_url` field in database
6. Return new logo URL

### 5.3 Image Processing

- **Library:** Pillow (`pip install Pillow`)
- **Resize:** Fit to 256×256, maintain aspect ratio, center crop
- **Format:** Convert all to WebP (smaller file size, good quality)
- **Quality:** WebP quality 85

### 5.4 Render Disk Configuration

See [Section 7](#7-render-disk-integration) for full disk setup.

### 5.5 URL Serving Strategy

- Mount `/var/data/uploads` as static files in FastAPI:
  ```
  app.mount("/uploads", StaticFiles(directory="/var/data/uploads"), name="uploads")
  ```
- `Club.logo_url` stores relative path: `/uploads/clubs/{club_id}/logo.webp`
- Add `Cache-Control: public, max-age=86400` header for logo files
- Frontend uses `logo_url` directly in `<img>` tags

**Files to create/modify:**
- `backend/app/models/models.py` — Add `logo_url: Optional[str]` to `Club`
- `backend/app/api/clubs.py` — Add upload/delete endpoints
- `backend/app/services/image.py` — NEW: image processing utility
- `backend/app/main.py` — Mount static files directory
- `requirements.txt` — Add `Pillow`

**Complexity: Medium**

---

## 6. Anti-Gaming

### 6.1 Detection Algorithms

#### Algorithm 1: Win Rate Anomaly
```
Flag if:
  - Player win rate > 85% over last 20 matches
  - AND average opponent rating < player_rating - 200
  → Possible farming weak opponents
```

#### Algorithm 2: Repeated Opponent Pattern
```
Flag if:
  - Same two players matched > 5 times in 7 days
  - AND one player always wins
  → Possible win trading
```

#### Algorithm 3: Match Frequency Spike
```
Flag if:
  - Player plays > 15 matches in 24 hours
  → Possible automation or farming
```

#### Algorithm 4: Rating Manipulation
```
Flag if:
  - Player's rating drops > 200 points in one session
  - THEN rises > 200 points in next session
  → Possible intentional losing then winning
```

#### Algorithm 5: Account Duplication
```
Flag if:
  - Two accounts share same device fingerprint / IP
  - AND play against each other
  → Possible multi-accounting
```

### 6.2 Risk Scoring System

| Factor | Weight | Threshold |
|--------|--------|-----------|
| Win rate anomaly | 30 | Score > 70 |
| Repeated opponents | 25 | Score > 70 |
| Match frequency | 20 | Score > 70 |
| Rating yo-yo | 15 | Score > 70 |
| Account similarity | 10 | Score > 70 |
| **Combined risk** | **100** | **Flag at > 60, auto-review at > 80** |

```
class RiskScore(SQLModel, table=True):
    __tablename__ = "risk_scores"
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    club_id: str = Field(foreign_key="clubs.id")
    score: float  # 0-100
    factors: str  # JSON breakdown
    calculated_at: datetime
    status: str  # clean, flagged, under_review, penalized
```

### 6.3 Automatic vs Manual Review

| Score Range | Action |
|-------------|--------|
| 0–40 | Clean — no action |
| 41–60 | Monitor — log but no action |
| 61–80 | Flag — notify club admins, add to review queue |
| 81–100 | Auto-restrict — temporarily prevent ranked matches, notify admins |

### 6.4 Penalty System

| Level | Trigger | Penalty | Duration |
|-------|---------|---------|----------|
| Warning | First flag (score 61-80) | Notification to player | — |
| Soft ban | Second flag or score > 80 | Matches don't count for rating | 7 days |
| Hard ban | Confirmed manipulation | Rating reset, removed from leaderboard | 30 days |
| Permanent | Repeated offenses | Account banned from club | Permanent |

### 6.5 Appeal Process

1. Player receives penalty notification with reason
2. Player submits appeal via `POST /appeals` with explanation
3. Club admin reviews in admin panel
4. Admin approves (penalty removed) or denies (penalty stands)
5. Super admin can override any decision

```
class Appeal(SQLModel, table=True):
    __tablename__ = "appeals"
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    risk_score_id: str = Field(foreign_key="risk_scores.id")
    reason: str
    status: str  # pending, approved, denied
    reviewed_by: Optional[str] = Field(foreign_key="users.id")
    reviewed_at: Optional[datetime]
    created_at: datetime
```

**Files to create:**
- `backend/app/models/models.py` — Add `RiskScore`, `Appeal` models
- `backend/app/services/anti_gaming.py` — NEW: detection algorithms
- `backend/app/api/admin.py` — Add review/appeal endpoints
- `frontend/src/app/clubs/[clubId]/admin/appeals/page.tsx` — NEW: review UI

**Complexity: Hard**

---

## 7. Render Disk Integration

### 7.1 Render.yaml Configuration

```yaml
services:
  - type: web
    name: badminton-api
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    disk:
      name: uploads
      mountPath: /var/data/uploads
      sizeGB: 1
    envVars:
      - key: UPLOAD_DIR
        value: /var/data/uploads
```

### 7.2 Disk Size Recommendation

| Content | Estimated Size |
|---------|---------------|
| Club logos (256×256 webp, ~20KB each) | 100 clubs × 20KB = 2MB |
| Original uploads (2MB max each) | 100 × 2MB = 200MB |
| Growth buffer | ~300MB |
| **Recommended:** | **1 GB** (Render minimum, sufficient for years) |

### 7.3 Mount Path Setup

- **Mount path:** `/var/data/uploads`
- **Environment variable:** `UPLOAD_DIR=/var/data/uploads`
- **In code:** Use `settings.UPLOAD_DIR` from config

```
# backend/app/core/config.py — add:
UPLOAD_DIR: str = "/var/data/uploads"
```

### 7.4 Code Changes Needed

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Add `UPLOAD_DIR` setting |
| `backend/app/main.py` | Mount `StaticFiles` at `/uploads` |
| `backend/app/main.py` | Create upload directory on startup if not exists |
| `render.yaml` | Add disk configuration |
| `requirements.txt` | Add `Pillow` for image processing |

### 7.5 Backup Strategy

- Render disks are **persistent but NOT backed up** by default
- Implement weekly backup:
  - Cron job (or Render cron) runs `tar czf backup.tar.gz /var/data/uploads`
  - Upload to S3/R2 bucket (cheap, reliable)
  - Keep last 4 weekly backups
- **Alternative:** Store logos in S3/Cloudflare R2 from the start (more resilient, slightly more complex)

---

## Implementation Priority

| Priority | Feature | Complexity | Impact | Phase |
|----------|---------|------------|--------|-------|
| 🔴 P0 | Bug #1: Club creation race condition | Easy | Critical — app broken | Phase 1 |
| 🔴 P0 | Bug #2: Phantom match history | Easy | High — misleading data | Phase 1 |
| 🟡 P1 | Admin system (Owner role) | Medium | High — needed for management | Phase 2 |
| 🟡 P1 | Club privacy (public/private toggle) | Medium | High — requested feature | Phase 2 |
| 🟡 P1 | Render disk integration | Easy | Required for logo upload | Phase 2 |
| 🟢 P2 | Logo upload | Medium | Medium — nice to have | Phase 2 |
| 🟢 P2 | Matchmaking / pair requests | Hard | Medium — advanced feature | Phase 3 |
| 🔵 P3 | Anti-gaming system | Hard | Low (until scale) | Phase 3 |

---

## Phase 1 (Quick Wins) — Est. 1-2 days

- [x] Fix Bug #1: Add explicit `await db.commit()` in `create_club` before returning
- [x] Fix Bug #1: Move cache invalidation after commit
- [x] Fix Bug #2: Remove hardcoded mock data in profile page
- [x] Fix Bug #2: Add empty state for charts when no match data

## Phase 2 (Core Features) — Est. 2-3 weeks

- [ ] Admin system: Add Owner role + permission checks
- [ ] Privacy: Public/private toggle + password join + QR invite
- [ ] Render disk: Configure disk + static file serving
- [ ] Logo upload: Image processing + upload endpoint
- [ ] Migration scripts for all schema changes

## Phase 3 (Advanced) — Est. 3-4 weeks

- [ ] Matchmaking: Pair request system + auto-pairing logic
- [ ] Anti-gaming: Detection algorithms + risk scoring
- [ ] Super admin panel
- [ ] Appeal system

---

## Technical Notes

1. **Database migrations:** All schema changes need Alembic migrations. Run `alembic revision --autogenerate` after model changes.

2. **Transaction safety:** The `get_db()` dependency commits after yield, but for operations that need immediate consistency (like create-then-redirect), use explicit `await db.commit()`.

3. **Cache strategy:** Current Redis cache uses pattern-based invalidation. For new features, ensure cache keys follow the `{entity}:{id}:{action}` pattern.

4. **QR code generation:** Use frontend library (`qrcode.react` or similar) — no backend QR generation needed. Backend just provides the invite code URL.

5. **WebSocket notifications:** Pair requests should trigger real-time notifications via the existing WebSocket infrastructure (`backend/app/websocket/socket_manager.py`).

6. **Thai language:** All user-facing strings in frontend are in Thai. Maintain this convention for new features.

7. **Rating system:** Current rating is simple (stored on User and ClubMember). Anti-gaming should analyze the Match table directly rather than relying on cached rating values.

8. **Render free tier limitations:** Free tier has no persistent disk. Must use at least Starter plan ($7/mo) for disk support.
