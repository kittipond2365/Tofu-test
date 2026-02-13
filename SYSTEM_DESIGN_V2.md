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

---

## Part 8: Advanced Features & Payment System

> Added: 2026-02-13 | Covers: Ownership Transfer, Role Refactor, Verified Clubs, Payment System, Match Types, Shuttlecock Tracking

---

### 8.1 Ownership Transfer System

**Flow:**
1. Current owner selects a club member from the transfer dropdown
2. Confirms the transfer (double-confirm dialog)
3. New owner receives full owner privileges immediately
4. Previous owner becomes either **regular member** or **moderator** (owner chooses before confirming)

**Database Fields (on Club table):**
```python
# Added to Club model
previous_owner_id: Optional[int] = Field(foreign_key="users.id")
transferred_at: Optional[datetime] = None
```

**API:**
```
POST /api/v1/clubs/{id}/transfer-ownership
Body: { "new_owner_id": int, "previous_owner_role": "member" | "moderator" }
Auth: Current Owner or Super Admin
```

**Backend Logic:**
1. Validate `new_owner_id` is an active club member
2. Begin transaction:
   - Update `Club.owner_id` → `new_owner_id`
   - Set `Club.previous_owner_id` → old owner id
   - Set `Club.transferred_at` → now
   - Update old owner's `ClubMember.role` → chosen role
   - If `previous_owner_role == "moderator"`: create `ClubModerator` record
   - Update new owner's `ClubMember.role` → `"owner"`
3. Commit + invalidate cache

---

### 8.2 Role System Refactor

**Previous roles:** Super Admin, Owner, Admin, Organizer, Member

**New role hierarchy:**

| Role | Scope | Description |
|------|-------|-------------|
| **Super Admin** | System | Full system access. Can hard reset, appoint admins. |
| **Admin** | System | Appointed by Super Admin only. Can do everything except hard reset and appoint other admins. Can verify clubs. |
| **Owner** | Club | Club creator/owner. Full club control. |
| **Club Moderator** | Club | Appointed by owner. Can manage sessions, players, results, shuttlecocks, edit club details. Cannot delete club. |
| **Player/Member** | Club | Regular member. Can join sessions, enter own match results, add shuttlecocks for self. |

#### 8.2.1 Club Moderator — Detailed Permissions

- ✅ Manage sessions (create, edit, cancel)
- ✅ Assign/remove players from sessions
- ✅ Edit club details (name, description, logo, payment settings, etc.)
- ✅ Enter match results (any match in club)
- ✅ Edit/correct match results
- ✅ Add/remove shuttlecocks during matches
- ✅ View payment calculations
- ❌ Delete club
- ❌ Transfer ownership
- ❌ Appoint other moderators

#### 8.2.2 Admin (System-level) — Detailed Permissions

- ✅ Everything Super Admin can do EXCEPT:
  - ❌ Hard reset system
  - ❌ Appoint other admins
- ✅ Verify/unverify clubs
- ✅ View admin messages from clubs
- ✅ Manage any club (edit, delete, etc.)
- ✅ Transfer any club's ownership

#### 8.2.3 Database: ClubModerator Table

```python
class ClubModerator(SQLModel, table=True):
    __tablename__ = "club_moderators"

    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    appointed_by: int = Field(foreign_key="users.id")
    appointed_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint: one moderator record per user per club
    __table_args__ = (
        UniqueConstraint('club_id', 'user_id', name='uq_club_moderator'),
    )
```

#### 8.2.4 Database: Admin Table (System-level)

```python
class Admin(SQLModel, table=True):
    __tablename__ = "admins"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    appointed_by: int = Field(foreign_key="users.id")
    appointed_at: datetime = Field(default_factory=datetime.utcnow)
    can_verify_clubs: bool = Field(default=True)
```

#### 8.2.5 API: Moderator Management

```
POST   /api/v1/clubs/{id}/moderators           — Appoint moderator
       Body: { "user_id": int }
       Auth: Owner or Super Admin

DELETE /api/v1/clubs/{id}/moderators/{user_id}  — Remove moderator
       Auth: Owner or Super Admin

GET    /api/v1/clubs/{id}/moderators            — List moderators
       Auth: Any club member
```

---

### 8.3 Verified Club System

#### 8.3.1 Verification Flow

```
[Unverified] ──(Club fills admin_message)──▶ [Pending Review]
                                                    │
                               Admin clicks verify  │  Admin clicks reject
                                    ▼                ▼
                              [Verified] ◄── [Unverified] (can retry)
                                    │
                          Admin clicks unverify
                                    ▼
                              [Unverified]
```

#### 8.3.2 Database Fields (on Club table)

```python
# Added to Club model
is_verified: bool = Field(default=False, index=True)
verified_by: Optional[int] = Field(default=None, foreign_key="users.id")
verified_at: Optional[datetime] = None
admin_message: Optional[str] = None  # Club's message to admins for verification review
```

#### 8.3.3 Verified Club Benefits

| Feature | Unverified Club | Verified Club |
|---------|----------------|---------------|
| Use app / create sessions | ✅ | ✅ |
| Record matches | ✅ | ✅ |
| Ranking system | ❌ Matches don't count | ✅ Full ranking |
| Anti-gaming monitoring | ❌ Not monitored | ✅ Active monitoring |
| Verified badge | ❌ | ✅ Badge displayed |
| Leaderboard eligible | ❌ | ✅ |

#### 8.3.4 API: Verification (Admin only)

```
POST /api/v1/admin/clubs/{id}/verify       — Verify a club
     Auth: Admin or Super Admin

POST /api/v1/admin/clubs/{id}/unverify     — Remove verification
     Auth: Admin or Super Admin

GET  /api/v1/admin/clubs/pending-verification — List clubs with admin_message set but not verified
     Auth: Admin or Super Admin
     Response: [{ club_id, club_name, admin_message, created_at, owner_name }]
```

#### 8.3.5 Ranking System Integration

```python
def on_match_complete(match, club):
    if club.is_verified:
        update_player_ranking(match.winner, match.loser, match.result)
        check_anti_gaming(match)
    else:
        # Record match but skip ranking & anti-gaming
        pass
```

#### 8.3.6 Anti-Gaming Update

All anti-gaming algorithms from Part 6 now have an additional gate:

```python
def run_anti_gaming_checks(match):
    club = get_club(match.club_id)
    if not club.is_verified:
        return  # Skip — unverified clubs not monitored
    # ... existing detection logic ...
```

---

### 8.4 Club Details (Editable Fields)

#### 8.4.1 Full Club Schema (Updated)

```python
class Club(SQLModel, table=True):
    # === Existing Fields ===
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    owner_id: int = Field(foreign_key="users.id")
    is_public: bool = Field(default=False)
    logo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # === NEW: Verification ===
    is_verified: bool = Field(default=False, index=True)
    verified_by: Optional[int] = Field(default=None, foreign_key="users.id")
    verified_at: Optional[datetime] = None
    admin_message: Optional[str] = None

    # === NEW: Payment Settings ===
    payment_type: str = Field(default="split")  # "split" | "shuttlecock" | "buffet"
    default_match_type: str = Field(default="single")  # "single" | "bo2" | "bo3"

    # === NEW: Shuttlecock Info ===
    shuttlecock_brand: Optional[str] = None  # e.g., "Yonex"
    shuttlecock_model: Optional[str] = None  # e.g., "AS-50"

    # === NEW: Ownership Transfer ===
    previous_owner_id: Optional[int] = Field(default=None, foreign_key="users.id")
    transferred_at: Optional[datetime] = None
```

#### 8.4.2 Editable Fields & Permissions

| Field | Owner | Moderator | Player | Admin |
|-------|:-----:|:---------:|:------:|:-----:|
| Club name | ✅ | ✅ | ❌ | ✅ |
| Description | ✅ | ✅ | ❌ | ✅ |
| Shuttlecock brand/model | ✅ | ✅ | ❌ | ✅ |
| Payment type | ✅ | ✅ | ❌ | ✅ |
| Default match type | ✅ | ✅ | ❌ | ✅ |
| Public/Private | ✅ | ✅ | ❌ | ✅ |
| Logo | ✅ | ✅ | ❌ | ✅ |
| Admin message | ✅ | ❌ | ❌ | ✅ (view only) |

---

### 8.5 Payment Calculation System

#### 8.5.1 Type A: Split by Time (หารตามเวลา)

**Concept:** Total court cost divided PROPORTIONALLY by each player's individual play time.

> ⚠️ **CORRECTED (2026-02-13):** Previously described as "split equally" with a single start time for all players. The correct behavior is proportional splitting based on individual play time.

**Session Setup:**
- Moderator/Owner enters `total_court_cost` (e.g., 900 THB)
- Each player has INDIVIDUAL play time (arrival/departure tracked separately)

**Calculation:**
```
Total minutes = Σ(each player's play minutes)
Cost per minute = Total Court Cost / Total minutes
Player cost = Player's minutes × Cost per minute
```

**Example:**
- Court cost: 300 THB/hour × 3 hours = 900 THB
- Player A: 120 min → (120/450) × 900 = **240 THB**
- Player B: 150 min → (150/450) × 900 = **300 THB**
- Player C: 180 min → (180/450) × 900 = **360 THB**
- Total minutes: 450, Total: 900 THB ✅

**Database (Session table additions):**
```python
# Added to Session model
total_court_cost: Optional[Decimal] = None
payment_type_override: Optional[str] = None  # Override club default
match_type_override: Optional[str] = None    # Override club default
```

**Database: Player Session Time Tracking**
```python
class PlayerSessionTime(SQLModel, table=True):
    __tablename__ = "player_session_times"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    play_minutes: int  # Total minutes this player played
    entered_by: int = Field(foreign_key="users.id")  # Moderator/Owner
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('session_id', 'player_id', name='uq_player_session_time'),
    )
```

---

#### 8.5.2 Type B: Per Shuttlecock (คิดตามลูก)

**Concept:** Fixed court fee per person + variable shuttlecock cost based on usage.

> ⚠️ **CORRECTED (2026-02-13):** Previously described court cost as varying by time. The correct behavior is a FIXED court fee per person, with only shuttlecock cost varying.

**Session Setup:**
- `fixed_court_fee_per_person` (e.g., 80 THB) — flat fee regardless of play time
- `shuttlecock_price_each` (e.g., 30 THB)
- These defaults come from club settings but can be overridden per session

**During Match — Shuttlecock Tracking:**
1. Any player on court (or moderator/owner) taps "Add Shuttlecock"
2. Confirmation dialog appears: "Add 1 shuttlecock? This will be shared by all 4 players on court."
3. On confirm → `ShuttlecockUsage` record created (confirmed=true)
4. Moderator can remove mistakenly added shuttlecocks

**Shuttlecock Cost Distribution:**
- Each shuttlecock is split among ALL 4 players on court at time of use
- Cost per player per shuttlecock = `shuttlecock_price_each / 4`

**Calculation:**
```
Player cost = Fixed Court Fee + (Player's shuttlecock share × Price per shuttlecock)
```

**Detailed Example:**
- Fixed court fee: 80 THB per person
- Shuttlecock price: 30 THB each
- Player A: 5 shuttlecocks used = 80 + (5 × 30 / 4) = 80 + 37.50 = **117.50 THB**
- Player B: 3 shuttlecocks used = 80 + (3 × 30 / 4) = 80 + 22.50 = **102.50 THB**

**Simplified Example (no per-court splitting):**
- If moderator tracks total shuttlecocks per player (not per match):
- Player A: 5 shuttlecocks = 80 + (5 × 30) = **230 THB**
- Player B: 3 shuttlecocks = 80 + (3 × 30) = **170 THB**

> **Note:** The moderator chooses whether shuttlecock costs are split per-court (÷4) or tracked as individual totals. Default: individual totals (simpler).

**Database: ShuttlecockUsage Table**
```python
class ShuttlecockUsage(SQLModel, table=True):
    __tablename__ = "shuttlecock_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    added_by: int = Field(foreign_key="users.id")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    quantity: int = Field(default=1)
    confirmed: bool = Field(default=False)
    confirmed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    removed: bool = Field(default=False)
    removed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    removed_at: Optional[datetime] = None
```

**API: Shuttlecock Tracking**
```
POST   /api/v1/matches/{id}/shuttlecocks                    — Add shuttlecock
       Body: { "quantity": 1 }
       Auth: Any player in match, Owner, or Moderator
       Response: { "usage_id": int, "confirmed": false }

POST   /api/v1/matches/{id}/shuttlecocks/{usage_id}/confirm — Confirm addition
       Auth: Same as above
       Response: { "confirmed": true }

DELETE /api/v1/matches/{id}/shuttlecocks/{usage_id}          — Remove (soft delete)
       Auth: Moderator or Owner only
       Response: { "removed": true }

GET    /api/v1/matches/{id}/shuttlecocks                     — List shuttlecocks for match
       Auth: Any player in match
       Response: [{ usage_id, quantity, added_by, confirmed, removed }]
```

---

#### 8.5.3 Type C: Buffet (บุฟเฟ่ — Flat Rate)

**Concept:** Fixed price per person. Owner/moderator tracks profit/loss.

**Session Setup:**
- `total_cost` — actual cost to book courts (e.g., 2000 THB)
- `flat_rate_per_person` — what each player pays (e.g., 300 THB)

**Calculation:**
```
Total Revenue = Flat Rate × Number of Players
Profit/Loss  = Total Revenue - Total Cost
```

**Example:**
- Total cost: 2000 THB, Flat rate: 300 THB, 8 players
- Revenue: 300 × 8 = 2400 THB
- Profit: 2400 - 2000 = +400 THB

**Display Rules:**
- **Players see:** "Your cost: 300 THB" (just the flat rate)
- **Owner/Moderator see:** Full breakdown with profit/loss

**Database (Session table additions):**
```python
# Added to Session model
buffet_total_cost: Optional[Decimal] = None
buffet_flat_rate: Optional[Decimal] = None
court_price_per_hour: Optional[Decimal] = None
shuttlecock_price_each: Optional[Decimal] = None
```

---

#### 8.5.4 PaymentCalculation Table (Computed Results)

```python
class PaymentCalculation(SQLModel, table=True):
    __tablename__ = "payment_calculations"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)

    # Cost breakdown
    court_cost: Decimal = Field(default=0)
    shuttlecock_cost: Decimal = Field(default=0)
    total_cost: Decimal = Field(default=0)

    # Details
    play_time_minutes: int = Field(default=0)
    shuttlecocks_used: int = Field(default=0)

    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('session_id', 'player_id', name='uq_payment_session_player'),
    )
```

#### 8.5.5 API: Payment Calculation

```
GET /api/v1/sessions/{id}/payments
    Auth: Owner or Moderator
    Response: {
      "payment_type": "split" | "shuttlecock" | "buffet",
      "players": [
        {
          "player_id": int,
          "player_name": str,
          "play_time_minutes": int,
          "shuttlecocks_used": int,
          "court_cost": "150.00",
          "shuttlecock_cost": "37.50",
          "total_cost": "187.50"
        }
      ],
      "session_total": "1500.00"
    }

GET /api/v1/sessions/{id}/payments/summary
    Auth: Owner or Moderator
    Response: {
      "payment_type": "buffet",
      "total_cost": "2000.00",
      "total_revenue": "2400.00",
      "profit_loss": "400.00",
      "player_count": 8,
      "per_player": "300.00"
    }
```

---

### 8.6 Match Types

#### 8.6.1 Supported Types

| Type | Sets | Win Condition |
|------|------|--------------|
| **Single Set** | 1 | Winner of 1 set wins |
| **Best of 2 (BO2)** | 2 | 2-0 = Win, 1-1 = Draw, 0-2 = Loss |
| **Best of 3 (BO3)** | Up to 3 | First to win 2 sets wins |

#### 8.6.2 Result Entry

**Who can enter:** Any player in the match, Owner, or Moderator

**How it works:**
1. After match completes, any authorized user taps "Enter Result"
2. For each set played, select the winning team (Team A or Team B)
3. No score entry needed — just the winner per set
4. Submit results

**Example — BO3 match:**
- Set 1: Team A wins → select "Team A"
- Set 2: Team B wins → select "Team B"
- Set 3: Team A wins → select "Team A"
- Result: Team A wins 2-1

**Correction:** Owner/Moderator can edit results after entry via "Edit Results" button.

#### 8.6.3 Database: Match Table Updates

```python
class Match(SQLModel, table=True):
    # === Existing fields ===
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    court_id: Optional[int] = None
    team_a_player1_id: int = Field(foreign_key="users.id")
    team_a_player2_id: int = Field(foreign_key="users.id")
    team_b_player1_id: int = Field(foreign_key="users.id")
    team_b_player2_id: int = Field(foreign_key="users.id")
    status: str = Field(default="pending")  # pending, in_progress, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # === NEW: Match Type & Results ===
    match_type: str = Field(default="single")  # "single" | "bo2" | "bo3"
    set1_winner_team: Optional[str] = None  # "A" or "B"
    set2_winner_team: Optional[str] = None  # "A" or "B" (BO2/BO3 only)
    set3_winner_team: Optional[str] = None  # "A" or "B" (BO3 only, if needed)

    # === NEW: Result Tracking ===
    result_entered_by: Optional[int] = Field(default=None, foreign_key="users.id")
    result_entered_at: Optional[datetime] = None
    result_modified_by: Optional[int] = Field(default=None, foreign_key="users.id")
    result_modified_at: Optional[datetime] = None

    # === Computed (from set results) ===
    @property
    def winner_team(self) -> Optional[str]:
        """Compute overall winner from set results."""
        if self.match_type == "single":
            return self.set1_winner_team
        elif self.match_type == "bo2":
            if self.set1_winner_team == self.set2_winner_team:
                return self.set1_winner_team  # 2-0
            return None  # 1-1 draw
        elif self.match_type == "bo3":
            wins = {"A": 0, "B": 0}
            for s in [self.set1_winner_team, self.set2_winner_team, self.set3_winner_team]:
                if s:
                    wins[s] += 1
            if wins["A"] >= 2:
                return "A"
            if wins["B"] >= 2:
                return "B"
            return None
```

#### 8.6.4 API: Match Results

```
POST /api/v1/matches/{id}/results
     Body: {
       "set1_winner": "A" | "B",
       "set2_winner": "A" | "B" | null,   # Required for BO2/BO3
       "set3_winner": "A" | "B" | null    # Required for BO3 if sets tied
     }
     Auth: Any player in the match, Owner, or Moderator
     Validation:
       - Single: only set1 allowed
       - BO2: set1 + set2 required, set3 must be null
       - BO3: set1 + set2 required; set3 required only if set1 ≠ set2

PUT  /api/v1/matches/{id}/results
     Body: same as POST
     Auth: Owner or Moderator ONLY
     Note: Updates result_modified_by and result_modified_at
```

---

### 8.7 Session Creation Flow

#### 8.7.1 Club Setup (One-time, in Club Settings)

| Setting | Field | Default |
|---------|-------|---------|
| Default payment type | `payment_type` | "split" |
| Default match type | `default_match_type` | "single" |
| Shuttlecock brand | `shuttlecock_brand` | null |
| Shuttlecock model | `shuttlecock_model` | null |
| Admin message | `admin_message` | null |

#### 8.7.2 Per-Session Setup

When creating a session, Owner/Moderator fills:

1. **Date & Time** — when the session takes place
2. **Court booking details** — court number, location, etc.
3. **Payment override** (optional checkbox):
   - If checked: select different payment type for this session
   - If unchecked: use club's default
4. **Match type override** (optional checkbox):
   - If checked: select different match type for this session
   - If unchecked: use club's default
5. **Payment-specific fields** (shown based on active payment type):
   - Type A (Split): `total_court_cost`
   - Type B (Shuttlecock): `court_price_per_hour`, `shuttlecock_price_each`
   - Type C (Buffet): `buffet_total_cost`, `buffet_flat_rate`

#### 8.7.3 Session Model Updates

```python
class Session(SQLModel, table=True):
    # === Existing fields ===
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id")
    created_by: int = Field(foreign_key="users.id")
    date: date
    start_time: Optional[time] = None
    status: str = Field(default="upcoming")  # upcoming, active, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # === NEW: Payment Override ===
    payment_type_override: Optional[str] = None  # null = use club default
    match_type_override: Optional[str] = None     # null = use club default

    # === NEW: Payment Details ===
    total_court_cost: Optional[Decimal] = None          # Type A
    fixed_court_fee_per_person: Optional[Decimal] = None  # Type B
    shuttlecock_price_each: Optional[Decimal] = None     # Type B
    buffet_total_cost: Optional[Decimal] = None          # Type C
    buffet_flat_rate: Optional[Decimal] = None           # Type C

    @property
    def effective_payment_type(self) -> str:
        return self.payment_type_override or self.club.payment_type

    @property
    def effective_match_type(self) -> str:
        return self.match_type_override or self.club.default_match_type
```

---

### 8.8 Permission Matrix (Complete)

| Action | Owner | Moderator | Player | Admin (System) | Super Admin |
|--------|:-----:|:---------:|:------:|:--------------:|:-----------:|
| Transfer Ownership | ✅ | ❌ | ❌ | ❌ | ✅ |
| Appoint Moderator | ✅ | ❌ | ❌ | ❌ | ✅ |
| Remove Moderator | ✅ | ❌ | ❌ | ❌ | ✅ |
| Edit Club Details | ✅ | ✅ | ❌ | ✅ | ✅ |
| Create Session | ✅ | ✅ | ❌ | ✅ | ✅ |
| Manage Payments | ✅ | ✅ | ❌ | ✅ | ✅ |
| Enter Match Results | ✅ | ✅ | ✅ *(own matches)* | ✅ | ✅ |
| Edit Match Results | ✅ | ✅ | ❌ | ✅ | ✅ |
| Add Shuttlecocks | ✅ | ✅ | ✅ *(own matches)* | ✅ | ✅ |
| Remove Shuttlecocks | ✅ | ✅ | ❌ | ✅ | ✅ |
| Verify Club | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Club | ✅ | ❌ | ❌ | ✅ | ✅ |
| Hard Reset System | ❌ | ❌ | ❌ | ❌ | ✅ |
| Appoint Admins | ❌ | ❌ | ❌ | ❌ | ✅ |
| View Admin Messages | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Payment Summary | ✅ | ✅ | ❌ | ✅ | ✅ |
| Export Payments | ✅ | ✅ | ❌ | ✅ | ✅ |

**Permission check utility:**
```python
# backend/app/core/permissions.py

def is_club_moderator(user_id: int, club_id: int, db: Session) -> bool:
    return db.query(ClubModerator).filter(
        ClubModerator.club_id == club_id,
        ClubModerator.user_id == user_id
    ).first() is not None

def is_system_admin(user_id: int, db: Session) -> bool:
    return db.query(Admin).filter(Admin.user_id == user_id).first() is not None

def can_manage_club(user_id: int, club_id: int, db: Session) -> bool:
    club = db.get(Club, club_id)
    if not club:
        return False
    return (
        club.owner_id == user_id
        or is_club_moderator(user_id, club_id, db)
        or is_system_admin(user_id, db)
        or is_super_admin(user_id, db)
    )
```

---

### 8.9 Frontend UI Components

#### 8.9.1 Club Settings Page

**Path:** `/clubs/[clubId]/settings`

```
┌─────────────────────────────────────┐
│ ⚙️ ตั้งค่าคลับ (Club Settings)        │
├─────────────────────────────────────┤
│ Club Name:    [___________________] │
│ Description:  [___________________] │
│ Logo:         [Upload] [Preview]    │
│ Public:       (●) Public (○) Private│
│                                     │
│ 🏸 Shuttlecock Info                  │
│ Brand:  [___________________]       │
│ Model:  [___________________]       │
│                                     │
│ 💰 Payment Type                      │
│ (●) หารเท่า (Split Equally)          │
│ (○) คิดตามลูก (Per Shuttlecock)      │
│ (○) บุฟเฟ่ (Buffet/Flat Rate)       │
│                                     │
│ 🎯 Default Match Type                │
│ (●) Single Set                      │
│ (○) Best of 2                       │
│ (○) Best of 3                       │
│                                     │
│ 👤 Transfer Ownership                │
│ New Owner: [Dropdown: members ▼]    │
│ Previous role: (●) Member (○) Mod   │
│ [Transfer Ownership]                │
│                                     │
│ 📝 Admin Message (for verification)  │
│ [________________________________] │
│ [________________________________] │
│ Status: ❌ Unverified                │
│                                     │
│ [Save Changes]                      │
└─────────────────────────────────────┘
```

#### 8.9.2 Session Creation Page

**Path:** `/clubs/[clubId]/sessions/create`

```
┌─────────────────────────────────────┐
│ 📅 สร้างเซสชัน (Create Session)      │
├─────────────────────────────────────┤
│ Date:  [__/__/____]                 │
│ Time:  [__:__]                      │
│ Court: [___________________]        │
│                                     │
│ ☐ Override payment type             │
│   → (shows payment selector if      │
│      checked)                       │
│                                     │
│ ☐ Override match type               │
│   → (shows match type selector if   │
│      checked)                       │
│                                     │
│ [Payment fields based on type:]     │
│                                     │
│ IF Split:                           │
│   Total Court Cost: [________] THB  │
│                                     │
│ IF Per Shuttlecock:                 │
│   Court fee/person:[______] THB    │
│   Shuttle price:   [______] THB    │
│                                     │
│ IF Buffet:                          │
│   Total Cost:  [________] THB      │
│   Price/person:[________] THB      │
│                                     │
│ [Create Session]                    │
└─────────────────────────────────────┘
```

#### 8.9.3 Match In Progress Page

```
┌─────────────────────────────────────┐
│ 🏸 Match #4 — Court 2               │
│ BO3 • Set 2 of 3                    │
├─────────────────────────────────────┤
│                                     │
│  Team A          vs        Team B   │
│  Player 1              Player 3     │
│  Player 2              Player 4     │
│                                     │
│  ⏱️ 00:23:15                        │
│                                     │
│  🟡 Shuttlecocks Used: 3            │
│  [+ Add Shuttlecock]                │
│  [- Remove] (moderator only)        │
│                                     │
│  ──────────────────────────         │
│  Set Results:                       │
│  Set 1: Team A ✅                   │
│  Set 2: [Team A] [Team B]          │
│  Set 3: (if needed)                │
│                                     │
│  [Submit Results]                   │
│  [Edit Results] (owner/mod)         │
└─────────────────────────────────────┘
```

**Add Shuttlecock Confirmation Dialog:**
```
┌─────────────────────────────┐
│ 🏸 เพิ่มลูกขนไก่?              │
│                             │
│ Add 1 shuttlecock?          │
│ This will be shared by all  │
│ 4 players on court.         │
│                             │
│ [Cancel]  [Confirm ✅]       │
└─────────────────────────────┘
```

#### 8.9.4 Match Result Entry

```
┌─────────────────────────────────────┐
│ 📝 Enter Match Result               │
├─────────────────────────────────────┤
│ Match Type: Best of 3               │
│                                     │
│ Set 1 Winner:                       │
│ [Team A ●]  [Team B ○]             │
│                                     │
│ Set 2 Winner:                       │
│ [Team A ○]  [Team B ●]             │
│                                     │
│ Set 3 Winner: (required — tied 1-1) │
│ [Team A ●]  [Team B ○]             │
│                                     │
│ Result: Team A wins 2-1             │
│                                     │
│ [Submit Result]                     │
└─────────────────────────────────────┘
```

#### 8.9.5 Payment Summary Page

**Path:** `/clubs/[clubId]/sessions/[sessionId]/payments`

```
┌──────────────────────────────────────────────────────────┐
│ 💰 Payment Summary — Session Feb 13, 2026                │
│ Payment Type: Per Shuttlecock (คิดตามลูก)                 │
├────────────┬──────────┬───────────┬───────────┬──────────┤
│ Player     │ Time     │ Shuttles  │ Court     │ Total    │
├────────────┼──────────┼───────────┼───────────┼──────────┤
│ สมชาย       │ 2h 30m   │ 8         │ ฿125.00   │ ฿175.00  │
│ สมหญิง      │ 2h 00m   │ 6         │ ฿100.00   │ ฿137.50  │
│ วิชัย        │ 1h 30m   │ 4         │ ฿75.00    │ ฿100.00  │
│ ...        │ ...      │ ...       │ ...       │ ...      │
├────────────┴──────────┴───────────┴───────────┴──────────┤
│ Total: ฿1,250.00                                         │
│                                                          │
│ [Export PDF]  [Export Excel]                              │
└──────────────────────────────────────────────────────────┘
```

**Buffet Summary (Owner/Moderator view):**
```
┌────────────────────────────────────┐
│ 💰 Buffet Summary                   │
│ Total Cost:    ฿2,000.00           │
│ Price/Person:  ฿300.00             │
│ Players:       8                   │
│ Revenue:       ฿2,400.00           │
│ Profit:        +฿400.00 ✅         │
└────────────────────────────────────┘
```

---

### 8.10 Complete API Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **Ownership** | | | |
| POST | `/api/v1/clubs/{id}/transfer-ownership` | Transfer ownership | Owner / Super Admin |
| **Moderators** | | | |
| POST | `/api/v1/clubs/{id}/moderators` | Appoint moderator | Owner / Super Admin |
| DELETE | `/api/v1/clubs/{id}/moderators/{user_id}` | Remove moderator | Owner / Super Admin |
| GET | `/api/v1/clubs/{id}/moderators` | List moderators | Club member |
| **Verification** | | | |
| POST | `/api/v1/admin/clubs/{id}/verify` | Verify club | Admin / Super Admin |
| POST | `/api/v1/admin/clubs/{id}/unverify` | Unverify club | Admin / Super Admin |
| GET | `/api/v1/admin/clubs/pending-verification` | List pending clubs | Admin / Super Admin |
| **Match Results** | | | |
| POST | `/api/v1/matches/{id}/results` | Enter results | Player in match / Owner / Mod |
| PUT | `/api/v1/matches/{id}/results` | Edit results | Owner / Moderator |
| **Shuttlecocks** | | | |
| POST | `/api/v1/matches/{id}/shuttlecocks` | Add shuttlecock | Player in match / Owner / Mod |
| POST | `/api/v1/matches/{id}/shuttlecocks/{uid}/confirm` | Confirm | Same as add |
| DELETE | `/api/v1/matches/{id}/shuttlecocks/{uid}` | Remove | Owner / Moderator |
| GET | `/api/v1/matches/{id}/shuttlecocks` | List for match | Player in match |
| **Payments** | | | |
| GET | `/api/v1/sessions/{id}/payments` | Calculate payments | Owner / Moderator |
| GET | `/api/v1/sessions/{id}/payments/summary` | Profit/loss summary | Owner / Moderator |

---

### 8.11 Implementation Phases

#### Phase 1: Core Structure (Est. 1–2 weeks)

| # | Task | Complexity | Dependencies |
|---|------|-----------|--------------|
| 1 | Database schema updates (Club, Session, Match new fields) | Medium | Alembic migrations |
| 2 | ClubModerator table + CRUD | Easy | #1 |
| 3 | Admin table + CRUD | Easy | #1 |
| 4 | Permission utility (`permissions.py`) refactor | Medium | #2, #3 |
| 5 | Verified club system (verify/unverify API) | Easy | #1, #3 |
| 6 | Club details update API (new editable fields) | Easy | #1 |
| 7 | Frontend: Club settings page update | Medium | #5, #6 |

#### Phase 2: Match & Payment (Est. 2–3 weeks)

| # | Task | Complexity | Dependencies |
|---|------|-----------|--------------|
| 8 | Match types (BO2/BO3) — model + API | Medium | #1 |
| 9 | Result entry system (POST/PUT results) | Medium | #8 |
| 10 | ShuttlecockUsage table + tracking API | Medium | #1 |
| 11 | Payment calculation engine (all 3 types) | Hard | #1, #10 |
| 12 | Session creation flow (override support) | Medium | #1, #11 |
| 13 | Frontend: Match result entry UI | Medium | #9 |
| 14 | Frontend: Shuttlecock tracking UI | Medium | #10 |
| 15 | Frontend: Payment summary page | Medium | #11 |
| 16 | Frontend: Session creation page update | Medium | #12 |

#### Phase 3: Advanced (Est. 1–2 weeks)

| # | Task | Complexity | Dependencies |
|---|------|-----------|--------------|
| 17 | Ownership transfer API | Medium | #1, #2 |
| 18 | Frontend: Transfer ownership UI | Easy | #17 |
| 19 | Anti-gaming: Add verified-club gate | Easy | #5 |
| 20 | Ranking: Add verified-club gate | Easy | #5 |
| 21 | Admin panel: Pending verification list | Medium | #5 |
| 22 | Payment export (PDF/Excel) | Medium | #11 |

**Total estimated time: 4–7 weeks**

---

### 8.12 Migration Script Outline

```python
"""Add advanced features & payment system

Revision ID: xxxx
"""

def upgrade():
    # 1. Club table additions
    op.add_column('clubs', sa.Column('is_verified', sa.Boolean(), default=False))
    op.add_column('clubs', sa.Column('verified_by', sa.Integer(), sa.ForeignKey('users.id')))
    op.add_column('clubs', sa.Column('verified_at', sa.DateTime()))
    op.add_column('clubs', sa.Column('admin_message', sa.Text()))
    op.add_column('clubs', sa.Column('payment_type', sa.String(20), default='split'))
    op.add_column('clubs', sa.Column('default_match_type', sa.String(10), default='single'))
    op.add_column('clubs', sa.Column('shuttlecock_brand', sa.String(100)))
    op.add_column('clubs', sa.Column('shuttlecock_model', sa.String(100)))
    op.add_column('clubs', sa.Column('previous_owner_id', sa.Integer(), sa.ForeignKey('users.id')))
    op.add_column('clubs', sa.Column('transferred_at', sa.DateTime()))
    op.add_column('clubs', sa.Column('payment_qr_url', sa.String(500)))
    op.add_column('clubs', sa.Column('payment_qr_uploaded_at', sa.DateTime()))
    op.add_column('clubs', sa.Column('payment_method_note', sa.String(200)))

    # 2. New tables
    op.create_table('club_moderators', ...)
    op.create_table('admins', ...)
    op.create_table('shuttlecock_usage', ...)
    op.create_table('player_session_times', ...)
    op.create_table('inbox_messages', ...)
    op.create_table('payment_proofs', ...)

    # 3. Match table additions
    op.add_column('matches', sa.Column('match_type', sa.String(10), default='single'))
    op.add_column('matches', sa.Column('set1_winner_team', sa.String(1)))
    op.add_column('matches', sa.Column('set2_winner_team', sa.String(1)))
    op.add_column('matches', sa.Column('set3_winner_team', sa.String(1)))
    op.add_column('matches', sa.Column('result_entered_by', sa.Integer(), sa.ForeignKey('users.id')))
    op.add_column('matches', sa.Column('result_entered_at', sa.DateTime()))
    op.add_column('matches', sa.Column('result_modified_by', sa.Integer(), sa.ForeignKey('users.id')))
    op.add_column('matches', sa.Column('result_modified_at', sa.DateTime()))

    # 4. Session table additions
    op.add_column('sessions', sa.Column('payment_type_override', sa.String(20)))
    op.add_column('sessions', sa.Column('match_type_override', sa.String(10)))
    op.add_column('sessions', sa.Column('total_court_cost', sa.Numeric(10, 2)))
    op.add_column('sessions', sa.Column('fixed_court_fee_per_person', sa.Numeric(10, 2)))
    op.add_column('sessions', sa.Column('shuttlecock_price_each', sa.Numeric(10, 2)))
    op.add_column('sessions', sa.Column('buffet_total_cost', sa.Numeric(10, 2)))
    op.add_column('sessions', sa.Column('buffet_flat_rate', sa.Numeric(10, 2)))

def downgrade():
    # Reverse all additions
    ...
```

---

### 8.13 Technical Notes

1. **Payment calculations are computed on-demand**, not stored permanently. The `PaymentCalculation` table serves as a cache/snapshot — recalculate when shuttlecocks or players change.

2. **Shuttlecock confirmation flow** prevents accidental additions. The `confirmed` flag must be `true` for the shuttlecock to count in payment calculations.

3. **Match type is set per-session** (with club default). Once a session is active, its match type cannot be changed (to prevent inconsistency with already-played matches).

4. **Verified status can be revoked.** If a club is unverified, all future matches stop counting for ranking, but historical ranking data is preserved.

5. **Ownership transfer is one-way and immediate.** No confirmation needed from the new owner (they receive a notification). The previous owner cannot undo the transfer.

6. **Admin message field** is only visible to system Admins and Super Admins. It's used by clubs to communicate why they should be verified (e.g., "We are an official badminton club at XYZ university with 50+ active members").

7. **Payment export** should support both PDF (for printing) and Excel (for further editing). Use `openpyxl` for Excel and `reportlab` or `weasyprint` for PDF generation.

8. **All monetary values use `Decimal`** (not float) to avoid floating-point precision issues in payment calculations.

---

### 8.14 Inbox / Notification System

**Purpose:** Centralized notification hub for payment requests, club invites, session reminders, and match results.

#### 8.14.1 Database Schema

```python
class InboxMessage(SQLModel, table=True):
    __tablename__ = "inbox_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str
    message: str
    message_type: str  # "payment", "notification", "invite", "result"

    # For payment messages
    amount: Optional[Decimal] = None
    qr_code_url: Optional[str] = None       # Club's payment QR (copied at send time)
    session_id: Optional[int] = Field(default=None, foreign_key="sessions.id")

    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 8.14.2 Message Types

| Type | Trigger | Content |
|------|---------|---------|
| `payment` | Session payment calculated | Amount owed + QR code |
| `notification` | System events | Session reminders, announcements |
| `invite` | Club invite sent | Club name + join link |
| `result` | Match completed | Match result summary |

#### 8.14.3 API Endpoints

```
GET    /api/v1/inbox                    — List user's messages (paginated)
       Query: ?type=payment&is_read=false&page=1&limit=20
       Auth: Authenticated user (own inbox only)

GET    /api/v1/inbox/unread-count       — Get unread count (for badge)
       Auth: Authenticated user

PATCH  /api/v1/inbox/{id}/read          — Mark as read
       Auth: Owner of message

PATCH  /api/v1/inbox/read-all           — Mark all as read
       Auth: Authenticated user

DELETE /api/v1/inbox/{id}               — Delete message
       Auth: Owner of message
```

#### 8.14.4 Frontend UI

```
┌─────────────────────────────────────┐
│ 📬 กล่องข้อความ (Inbox)        [3]   │
├─────────────────────────────────────┤
│ [All] [💰 Payment] [🔔 Notif] [📊]  │
├─────────────────────────────────────┤
│ 🔴 ค่าใช้จ่ายสนาม - 13 ก.พ. 2026    │
│    คุณต้องชำระเงิน 230 บาท           │
│    2 ชั่วโมงที่แล้ว                      │
├─────────────────────────────────────┤
│ 🔴 ผลการแข่งขัน Match #4            │
│    Team A ชนะ 2-1                   │
│    3 ชั่วโมงที่แล้ว                      │
├─────────────────────────────────────┤
│ ○  เชิญเข้าร่วมคลับ "Smash Club"    │
│    5 วันที่แล้ว                          │
└─────────────────────────────────────┘
```

**Payment Message Detail:**
```
┌─────────────────────────────────────┐
│ 💰 ค่าใช้จ่ายสนาม - 13 ก.พ. 2026    │
├─────────────────────────────────────┤
│ คุณต้องชำระเงิน                       │
│                                     │
│ ┌─────────────────────┐             │
│ │    230.00 บาท       │             │
│ └─────────────────────┘             │
│                                     │
│ 📱 สแกน QR เพื่อชำระเงิน:             │
│ ┌─────────────┐                     │
│ │  [QR CODE]  │                     │
│ │  PromptPay  │                     │
│ └─────────────┘                     │
│ หมายเหตุ: PromptPay 081-234-5678    │
│                                     │
│ [📸 อัพโหลดสลิป]                     │
│                                     │
│ Session: Feb 13, 2026 →             │
└─────────────────────────────────────┘
```

---

### 8.15 Owner QR Code Upload & Payment Flow

#### 8.15.1 Club Payment Settings (Updated)

```python
class Club(SQLModel, table=True):
    # ... existing fields ...

    # === NEW: Payment QR ===
    payment_qr_url: Optional[str] = None          # Uploaded QR image URL
    payment_qr_uploaded_at: Optional[datetime] = None
    payment_method_note: Optional[str] = None      # e.g., "PromptPay: 081-234-5678"
```

#### 8.15.2 QR Upload API

```
POST   /api/v1/clubs/{id}/payment-qr     — Upload payment QR image
       Content-Type: multipart/form-data
       Body: file (image), payment_method_note (optional)
       Auth: Owner or Moderator
       Process: Validate image → save to /var/data/uploads/clubs/{id}/payment_qr.webp
       Response: { "qr_url": "/uploads/clubs/{id}/payment_qr.webp" }

DELETE /api/v1/clubs/{id}/payment-qr     — Remove payment QR
       Auth: Owner or Moderator

GET    /api/v1/clubs/{id}/payment-qr     — Get QR info
       Auth: Club member
       Response: { "qr_url": "...", "note": "PromptPay: 081-234-5678" }
```

#### 8.15.3 Payment Proof System

```python
class PaymentProof(SQLModel, table=True):
    __tablename__ = "payment_proofs"

    id: Optional[int] = Field(default=None, primary_key=True)
    inbox_message_id: int = Field(foreign_key="inbox_messages.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    image_url: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # uploaded_at + 30 days

    # Cleanup: daily cron job deletes expired proofs (image + record)
```

#### 8.15.4 Payment Proof API

```
POST   /api/v1/inbox/{id}/proof           — Upload payment proof (slip image)
       Content-Type: multipart/form-data
       Auth: Owner of inbox message
       Process: Validate → save image → set expires_at = now + 30 days
       Response: { "proof_id": int, "expires_at": datetime }

GET    /api/v1/inbox/{id}/proof            — View proof image
       Auth: Message owner, Club owner, or Moderator

DELETE /api/v1/inbox/{id}/proof            — Delete proof manually
       Auth: Message owner
```

#### 8.15.5 Complete Payment Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    PAYMENT FLOW                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. SESSION ENDS                                             │
│     │                                                        │
│     ▼                                                        │
│  2. MODERATOR clicks "Calculate Payments"                    │
│     │  System calculates per player (Type A/B/C)             │
│     │                                                        │
│     ▼                                                        │
│  3. MODERATOR clicks "Send Payment Requests"                 │
│     │  System creates InboxMessage for each player           │
│     │  Includes: amount, QR code (if uploaded), session link │
│     │                                                        │
│     ▼                                                        │
│  4. PLAYER opens Inbox → sees payment message                │
│     │  Scans QR code → pays via PromptPay/bank              │
│     │                                                        │
│     ▼                                                        │
│  5. PLAYER uploads payment proof (bank slip screenshot)      │
│     │  Proof stored with 30-day expiry                       │
│     │                                                        │
│     ▼                                                        │
│  6. OWNER/MODERATOR views proofs in session payment summary  │
│     │  Confirms payments received                            │
│     │                                                        │
│     ▼                                                        │
│  7. CLEANUP: Daily job deletes expired proofs (>30 days)     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 8.15.6 Send Payment Requests API

```
POST /api/v1/sessions/{id}/payments/send    — Send payment messages to all players
     Auth: Owner or Moderator
     Process:
       1. Calculate payments for all players
       2. Get club's payment QR URL
       3. Create InboxMessage for each player:
          - title: "ค่าใช้จ่ายสนาม - {date}"
          - message: "คุณต้องชำระเงิน {amount} บาท"
          - amount: calculated amount
          - qr_code_url: club.payment_qr_url
          - session_id: session.id
          - message_type: "payment"
     Response: { "sent_count": int, "players": [...] }
```

#### 8.15.7 Payment Summary (Updated with Proof Status)

```
┌──────────────────────────────────────────────────────────────┐
│ 💰 Payment Summary — Session Feb 13, 2026                    │
│ Payment Type: คิดตามลูก (Per Shuttlecock)                     │
├────────────┬──────────┬───────────┬──────────┬───────────────┤
│ Player     │ Court    │ Shuttle   │ Total    │ Proof         │
├────────────┼──────────┼───────────┼──────────┼───────────────┤
│ สมชาย       │ ฿80      │ ฿150      │ ฿230     │ ✅ Uploaded    │
│ สมหญิง      │ ฿80      │ ฿90       │ ฿170     │ ⏳ Pending     │
│ วิชัย        │ ฿80      │ ฿120      │ ฿200     │ ❌ Not sent    │
├────────────┴──────────┴───────────┴──────────┴───────────────┤
│ [Send Payment Requests]  [View Proofs]                       │
└──────────────────────────────────────────────────────────────┘
```

---

### 8.16 Audit & Simplification Report

> Added: 2026-02-13 | Purpose: Review design for redundancy, complexity, and simplification opportunities

#### 8.16.1 Removed: PaymentCalculation Table

**Before:** Separate `PaymentCalculation` table storing computed results.

**After:** Calculate on-the-fly. No stored payment results.

**Reason:** Payment amounts depend on player times and shuttlecock counts which can change. Storing computed values creates stale data risk. Calculate fresh on each `GET /sessions/{id}/payments` call.

**Impact:** Remove `payment_calculations` table entirely. Payment endpoint computes and returns results without persisting.

#### 8.16.2 Simplified: Shuttlecock Tracking

**Before:** Complex per-match tracking with confirmed/removed flags and per-court splitting.

**After:** Simple per-player count entered by moderator at session end.

```python
class ShuttlecockUsage(SQLModel, table=True):
    __tablename__ = "shuttlecock_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    quantity: int = Field(default=0)
    entered_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint('session_id', 'player_id', name='uq_shuttle_session_player'),
    )
```

**Removed fields:** `match_id`, `confirmed`, `confirmed_by`, `removed`, `removed_by`, `removed_at`

**Reason:** Real-world usage shows moderators count total shuttlecocks per player at session end, not track individually per match. Simpler = fewer bugs.

#### 8.16.3 Simplified: Session Model

**Removed fields:**
- `session_start_time` — not needed (individual times tracked in `PlayerSessionTime`)
- `court_price_per_hour` — replaced with `fixed_court_fee_per_person` for Type B

**Updated Session fields:**
```python
class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id")
    created_by: int = Field(foreign_key="users.id")
    date: date
    start_time: Optional[time] = None
    status: str = Field(default="upcoming")  # upcoming, active, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Payment override (null = use club default)
    payment_type_override: Optional[str] = None
    match_type_override: Optional[str] = None

    # Type A: Split by Time
    total_court_cost: Optional[Decimal] = None

    # Type B: Per Shuttlecock
    fixed_court_fee_per_person: Optional[Decimal] = None
    shuttlecock_price_each: Optional[Decimal] = None

    # Type C: Buffet
    buffet_total_cost: Optional[Decimal] = None
    buffet_flat_rate: Optional[Decimal] = None
```

#### 8.16.4 Consolidated API Endpoints

**Before:** 30+ endpoints across many routers.

**After:** Consolidated to clear groups:

| Group | Endpoints | Notes |
|-------|-----------|-------|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | 3 endpoints |
| **Clubs** | `CRUD /clubs`, `PATCH /clubs/{id}`, `POST /clubs/{id}/join`, `POST /clubs/{id}/transfer-ownership` | 6 endpoints |
| **Club Members** | `GET /clubs/{id}/members`, `PATCH /clubs/{id}/members/{uid}/role`, `DELETE /clubs/{id}/members/{uid}` | 3 endpoints |
| **Club Moderators** | `POST/DELETE/GET /clubs/{id}/moderators` | 3 endpoints |
| **Club Payment** | `POST/DELETE/GET /clubs/{id}/payment-qr` | 3 endpoints |
| **Sessions** | `CRUD /sessions`, `GET /sessions/{id}/players` | 5 endpoints |
| **Session Payments** | `GET /sessions/{id}/payments`, `POST /sessions/{id}/payments/send` | 2 endpoints |
| **Player Time** | `POST/PUT /sessions/{id}/player-times` (batch) | 1 endpoint (batch) |
| **Shuttlecocks** | `POST/PUT /sessions/{id}/shuttlecocks` (batch) | 1 endpoint (batch) |
| **Matches** | `POST /matches/{id}/results`, `PUT /matches/{id}/results` | 2 endpoints |
| **Inbox** | `GET /inbox`, `GET /inbox/unread-count`, `PATCH /inbox/{id}/read`, `POST /inbox/{id}/proof` | 5 endpoints |
| **Admin** | `POST /admin/clubs/{id}/verify`, `GET /admin/clubs/pending` | 3 endpoints |
| **Privacy** | `POST /clubs/{id}/invite-code`, `POST /clubs/join-by-code`, `POST /clubs/{id}/join-by-password` | 3 endpoints |
| **Pairs** | `POST/GET /clubs/{id}/pairs`, `POST /pairs/requests/{id}/accept` | 5 endpoints |
| **Total** | | **~45 endpoints** |

#### 8.16.5 Naming Consistency

| Old | New | Reason |
|-----|-----|--------|
| `Organizer` role | Removed | Merged into `Moderator` |
| `Admin` (club-level) | `Moderator` | Clearer distinction from system Admin |
| `court_price_per_hour` | `fixed_court_fee_per_person` | Reflects actual behavior |
| `PaymentCalculation` table | Removed | Compute on-the-fly |
| `session_start_time` | Removed | Use `PlayerSessionTime` instead |

#### 8.16.6 Clean Database Schema Summary

**Tables (13 total):**

| # | Table | Purpose |
|---|-------|---------|
| 1 | `users` | User accounts |
| 2 | `clubs` | Club info + settings + payment QR |
| 3 | `club_members` | Club membership + role |
| 4 | `club_moderators` | Moderator appointments |
| 5 | `admins` | System-level admins |
| 6 | `sessions` | Play sessions |
| 7 | `matches` | Individual matches within sessions |
| 8 | `player_session_times` | Per-player play time (Type A) |
| 9 | `shuttlecock_usage` | Per-player shuttle count (Type B) |
| 10 | `inbox_messages` | Notifications & payment requests |
| 11 | `payment_proofs` | Payment slip uploads (30-day expiry) |
| 12 | `pair_requests` | Matchmaking pair requests |
| 13 | `active_pairs` | Active player pairs |

**Removed tables:**
- `payment_calculations` — compute on-the-fly
- `risk_scores` — defer to Phase 4 (anti-gaming)
- `appeals` — defer to Phase 4

#### 8.16.7 UI/UX Simplification

**Principle:** Fewer clicks for common tasks. Mobile-first.

| Task | Before | After |
|------|--------|-------|
| Calculate payments | Navigate to session → payments tab → click calculate | Session end → auto-prompt "Calculate payments?" |
| Enter shuttlecock count | Per match, per shuttlecock, with confirmation | Batch entry: moderator enters count per player at session end |
| Enter play time | Complex time picker per player | Simple minutes input per player |
| Pay for session | No in-app flow | Inbox → QR → scan → upload proof |
| Check payment status | Not available | Payment summary shows proof status per player |

**Quick Actions (Session Page):**
```
┌─────────────────────────────────────┐
│ Session: Feb 13, 2026  [Active]     │
├─────────────────────────────────────┤
│ ⚡ Quick Actions:                    │
│ [🏸 New Match] [⏹ End Session]      │
│ [💰 Payments]  [📊 Summary]         │
└─────────────────────────────────────┘
```

#### 8.16.8 Updated Implementation Phases

| Phase | Features | Est. Time |
|-------|----------|-----------|
| **Phase 1** | Bug fixes (done) | ✅ Done |
| **Phase 2** | Roles, permissions, club settings, verified clubs | 1-2 weeks |
| **Phase 3** | Payment system (Type A/B/C), inbox, QR upload, payment proofs | 2-3 weeks |
| **Phase 4** | Matchmaking pairs, anti-gaming, advanced admin | 2-3 weeks |
| **Total** | | **5-8 weeks** |
