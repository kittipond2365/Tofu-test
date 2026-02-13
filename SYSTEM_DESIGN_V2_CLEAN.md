# Badminton Club Management System — Design Document V2

> Generated: 2026-02-13 | Status: Design Document (No Implementation Code)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Bug Fixes Required](#2-bug-fixes-required)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Feature: Club System](#4-feature-club-system)
5. [Feature: Session Management](#5-feature-session-management)
6. [Feature: Match System](#6-feature-match-system)
7. [Feature: Payment System](#7-feature-payment-system)
8. [Feature: Inbox & Notifications](#8-feature-inbox--notifications)
9. [Feature: Matchmaking & Pairs](#9-feature-matchmaking--pairs)
10. [Feature: Privacy & Invites](#10-feature-privacy--invites)
11. [Feature: Anti-Gaming](#11-feature-anti-gaming)
12. [Database Schema](#12-database-schema)
13. [API Endpoints](#13-api-endpoints)
14. [Frontend UI](#14-frontend-ui)
15. [Infrastructure](#15-infrastructure)
16. [Implementation Plan](#16-implementation-plan)
17. [Technical Notes](#17-technical-notes)

---

## 1. Executive Summary

A badminton club management app covering club creation, session/match management, three payment calculation types (split-by-time, per-shuttlecock, buffet), player pairing/matchmaking, club privacy controls, an inbox notification system with QR payment flow, and anti-gaming detection for verified clubs. Built with FastAPI (Python) + Next.js frontend, deployed on Render with persistent disk for file uploads.

---

## 2. Bug Fixes Required

### 2.1 Club Creation — "Not Found" Error

- **Symptom:** Create club → API returns 200 → navigate to club → "Club not found"
- **Root Cause:** `create_club` calls `db.flush()` (not `db.commit()`). Response returns before commit completes. Frontend navigates immediately → new DB session can't find uncommitted data. Cache is also invalidated before commit.
- **Fix:**

| Step | File | Change |
|------|------|--------|
| 1 | `backend/app/api/clubs.py` | Add explicit `await db.commit()` after creating club + member, THEN invalidate cache |
| 2 | `backend/app/api/clubs.py` | Add `await db.refresh(new_club)` after commit |
| 3 | `frontend/src/app/clubs/create/page.tsx` | Await `queryClient.invalidateQueries` before navigation |

### 2.2 Phantom Match History

- **Symptom:** New user (never played) sees match history graph with matches > 0
- **Root Cause:** Frontend `profile/page.tsx` has hardcoded mock arrays (`ratingHistory`, `matchesPerMonth`) that render for all users. No backend endpoint exists for monthly match history.
- **Fix:**

| Step | File | Change |
|------|------|--------|
| 1 | `frontend/src/app/profile/page.tsx` | Remove hardcoded mock arrays |
| 2 | `backend/app/api/stats.py` | Add `GET /users/{user_id}/match-history` endpoint |
| 3 | `frontend/src/app/profile/page.tsx` | Fetch real data; show empty state when no matches |

---

## 3. User Roles & Permissions

### 3.1 Role Hierarchy

| Role | Scope | Description |
|------|-------|-------------|
| **Super Admin** | System | Full system access. Hard reset, appoint admins. |
| **Admin** | System | Appointed by Super Admin. Everything except hard reset & appointing admins. Can verify clubs. |
| **Owner** | Club | Club creator. Full club control. |
| **Moderator** | Club | Appointed by Owner. Manage sessions, players, results, shuttlecocks, edit club details. |
| **Player/Member** | Club | Join sessions, enter own match results, add shuttlecocks for own matches. |

### 3.2 Permission Matrix

| Action | Super Admin | Admin | Owner | Moderator | Player |
|--------|:-----------:|:-----:|:-----:|:---------:|:------:|
| Hard reset system | ✅ | ❌ | ❌ | ❌ | ❌ |
| Appoint system admins | ✅ | ❌ | ❌ | ❌ | ❌ |
| Verify/unverify clubs | ✅ | ✅ | ❌ | ❌ | ❌ |
| View admin messages | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete any club | ✅ | ✅ | ❌ | ❌ | ❌ |
| Transfer any club ownership | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete own club | ✅ | ✅ | ✅ | ❌ | ❌ |
| Transfer own club ownership | ✅ | — | ✅ | ❌ | ❌ |
| Appoint/remove moderators | ✅ | — | ✅ | ❌ | ❌ |
| Edit club details | ✅ | ✅ | ✅ | ✅ | ❌ |
| Create/manage sessions | ✅ | ✅ | ✅ | ✅ | ❌ |
| Manage payments | ✅ | ✅ | ✅ | ✅ | ❌ |
| Edit match results | ✅ | ✅ | ✅ | ✅ | ❌ |
| Remove shuttlecocks | ✅ | ✅ | ✅ | ✅ | ❌ |
| Enter match results (own) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Add shuttlecocks (own) | ✅ | ✅ | ✅ | ✅ | ✅ |
| View club / join sessions | ✅ | ✅ | ✅ | ✅ | ✅ |

### 3.3 Database Tables

```python
class Admin(SQLModel, table=True):
    __tablename__ = "admins"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    appointed_by: int = Field(foreign_key="users.id")
    appointed_at: datetime
    can_verify_clubs: bool = Field(default=True)

class ClubModerator(SQLModel, table=True):
    __tablename__ = "club_moderators"
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    appointed_by: int = Field(foreign_key="users.id")
    appointed_at: datetime
    __table_args__ = (UniqueConstraint('club_id', 'user_id', name='uq_club_moderator'),)
```

### 3.4 Permission Check Utility

```python
# backend/app/core/permissions.py
def can_manage_club(user_id, club_id, db) -> bool:
    club = db.get(Club, club_id)
    return (club.owner_id == user_id
            or is_club_moderator(user_id, club_id, db)
            or is_system_admin(user_id, db)
            or is_super_admin(user_id, db))
```

---

## 4. Feature: Club System

### 4.1 Club Creation

- User creates club → becomes Owner automatically
- `ClubMember` record created with `role="owner"`
- Club defaults: `is_public=False`, `payment_type="split"`, `default_match_type="single"`

### 4.2 Club Verification

**Flow:**
```
[Unverified] → Owner writes admin_message → [Pending Review]
  → Admin verifies → [Verified] (or rejects → can retry)
  → Admin can unverify later
```

**Benefits of verification:**

| Feature | Unverified | Verified |
|---------|:----------:|:--------:|
| Use app / create sessions | ✅ | ✅ |
| Record matches | ✅ | ✅ |
| Ranking system | ❌ | ✅ |
| Anti-gaming monitoring | ❌ | ✅ |
| Verified badge | ❌ | ✅ |
| Leaderboard eligible | ❌ | ✅ |

### 4.3 Ownership Transfer

1. Owner selects member → double-confirm dialog
2. New owner gets full privileges immediately
3. Previous owner becomes member or moderator (owner chooses)
4. One-way and immediate — no undo

### 4.4 Editable Club Fields

| Field | Owner | Moderator | Player |
|-------|:-----:|:---------:|:------:|
| Name, Description | ✅ | ✅ | ❌ |
| Logo | ✅ | ✅ | ❌ |
| Public/Private | ✅ | ✅ | ❌ |
| Payment type, Match type | ✅ | ✅ | ❌ |
| Shuttlecock brand/model | ✅ | ✅ | ❌ |
| Admin message | ✅ | ❌ | ❌ |
| Payment QR | ✅ | ✅ | ❌ |

### 4.5 Logo Upload

- **Endpoint:** `POST /clubs/{club_id}/logo` (multipart/form-data)
- **Validation:** ≤ 2MB, jpg/png/webp only
- **Processing:** Resize 256×256, convert to WebP (quality 85) via Pillow
- **Storage:** `/var/data/uploads/clubs/{club_id}/logo.webp`
- **Serving:** Mounted as static files at `/uploads/`

---

## 5. Feature: Session Management

### 5.1 Session Creation

Owner/Moderator fills:
1. **Date & Time**
2. **Court booking details**
3. **Payment type override** (optional — defaults to club setting)
4. **Match type override** (optional — defaults to club setting)
5. **Payment-specific fields** (based on active payment type):
   - Type A (Split): `total_court_cost`
   - Type B (Shuttlecock): `fixed_court_fee_per_person`, `shuttlecock_price_each`
   - Type C (Buffet): `buffet_total_cost`, `buffet_flat_rate`

### 5.2 Session Lifecycle

```
[Upcoming] → [Active] → [Completed]
```

- Once active, match type cannot change (prevents inconsistency)
- On session end, auto-prompt "Calculate payments?"

---

## 6. Feature: Match System

### 6.1 Match Types

| Type | Sets | Win Condition |
|------|------|---------------|
| **Single Set** | 1 | Winner of 1 set wins |
| **Best of 2** | 2 | 2-0 = Win, 1-1 = Draw |
| **Best of 3** | Up to 3 | First to win 2 sets |

### 6.2 Result Entry

- **Who can enter:** Any player in the match, Owner, or Moderator
- **How:** Select winning team (A or B) per set — no score entry needed
- **Correction:** Owner/Moderator can edit results after entry

**Example — BO3:**
- Set 1: Team A wins → Set 2: Team B wins → Set 3: Team A wins → Result: Team A wins 2-1

### 6.3 Shuttlecock Tracking

Simplified: Moderator enters total shuttlecock count per player at session end (batch entry), not per-match tracking.

---

## 7. Feature: Payment System

### 7.1 Type A: Split by Time (หารตามเวลา)

**Concept:** Total court cost split proportionally by each player's play time.

**Formula:**
```
Cost per minute = Total Court Cost / Σ(all player minutes)
Player cost = Player's minutes × Cost per minute
```

**Example:**
- Court cost: 900 THB (300/hr × 3hr)
- Player A: 120 min → (120/450) × 900 = **240 THB**
- Player B: 150 min → (150/450) × 900 = **300 THB**
- Player C: 180 min → (180/450) × 900 = **360 THB**
- Total minutes: 450 → Total: 900 THB ✅

**Data needed:** Moderator enters play minutes per player via `PlayerSessionTime` table.

### 7.2 Type B: Per Shuttlecock (คิดตามลูก)

**Concept:** Fixed court fee per person + shuttlecock cost per player.

**Formula:**
```
Player cost = Fixed Court Fee + (Shuttlecocks Used × Price Each)
```

**Example:**
- Fixed court fee: 80 THB/person
- Shuttle price: 30 THB each
- Player A (5 shuttles): 80 + 150 = **230 THB**
- Player B (3 shuttles): 80 + 90 = **170 THB**

**Data needed:** Moderator enters shuttlecock count per player via `ShuttlecockUsage` table.

### 7.3 Type C: Buffet (บุฟเฟ่ — Flat Rate)

**Concept:** Fixed price per person. Owner tracks profit/loss.

**Formula:**
```
Player cost = Flat Rate
Revenue = Flat Rate × Number of Players
Profit/Loss = Revenue - Total Cost
```

**Example:**
- Total cost: 2,000 THB | Flat rate: 300 THB | 8 players
- Revenue: 300 × 8 = 2,400 THB
- Profit: +400 THB

**Display rules:**
- Players see: "Your cost: 300 THB"
- Owner/Moderator see: Full breakdown with profit/loss

### 7.4 Payment QR & Proof Flow

```
1. SESSION ENDS
   ▼
2. Moderator clicks "Calculate Payments"
   → System calculates per player (Type A/B/C)
   ▼
3. Moderator clicks "Send Payment Requests"
   → Creates InboxMessage per player (amount + QR code + session link)
   ▼
4. Player opens Inbox → sees amount + QR code
   → Scans QR → pays via PromptPay/bank
   ▼
5. Player uploads payment proof (bank slip)
   → Stored with 30-day auto-expiry
   ▼
6. Owner/Moderator views proofs in payment summary
   ▼
7. Daily cleanup job deletes expired proofs (>30 days)
```

**Payment QR:** Owner uploads club payment QR image (PromptPay etc.) in club settings. Stored at `/var/data/uploads/clubs/{id}/payment_qr.webp`.

### 7.5 Design Decisions

- **Payments computed on-the-fly** (no `PaymentCalculation` table) — avoids stale data
- **All monetary values use `Decimal`** — no floating-point errors
- **Shuttlecock counts are per-player per-session** (not per-match) — simpler, matches real usage

---

## 8. Feature: Inbox & Notifications

### 8.1 Message Types

| Type | Trigger | Content |
|------|---------|---------|
| `payment` | Payment calculated | Amount owed + QR code |
| `notification` | System events | Session reminders, announcements |
| `invite` | Club invite | Club name + join link |
| `result` | Match completed | Match result summary |

### 8.2 Payment Proof

- Player uploads bank slip screenshot from inbox message
- Stored with 30-day auto-expiry
- Viewable by: message owner, club owner, moderator

---

## 9. Feature: Matchmaking & Pairs

### 9.1 Pair Request State Machine

```
[No Relationship] → Player A sends request → [PENDING]
  → Player B accepts → [ACCEPTED]
  → Player B rejects / expires (7 days) → [REJECTED] → can re-request
  → Either cancels → [CANCELLED]
```

### 9.2 Match Generation with Pairs

1. Get registered players for session
2. Find active pairs where BOTH players are registered
3. Place paired players on same team first
4. Remaining players: rating-based matchmaking
5. Balance check on combined ratings

### 9.3 Edge Cases

| Case | Handling |
|------|----------|
| One paired player absent | Other goes to regular pool |
| Player in multiple pairs | System picks best match by availability |
| Request to non-member | Reject: "Must be in same club" |
| Self-request | Reject |
| Request expires (7 days) | Auto-reject via background task |

---

## 10. Feature: Privacy & Invites

### 10.1 Club Visibility

- **Public clubs:** Appear in search results (`GET /clubs/search`)
- **Private clubs:** Never in search. Accessible only via invite code or password.

### 10.2 Join Methods

| Method | For | Flow |
|--------|-----|------|
| Direct join | Public clubs | Click "Join" → instant |
| Password | Private clubs | Enter password → join |
| QR/Invite code | Private clubs | Scan QR → opens join URL → join |

### 10.3 QR Invite Flow

1. Owner generates invite code (`POST /clubs/{id}/invite-code`) — 12-char nanoid, 7-day expiry
2. Frontend renders QR containing `https://app.example.com/clubs/join?code={code}`
3. User scans → `POST /clubs/join-by-code` → validates code + expiry → creates membership

---

## 11. Feature: Anti-Gaming

> Only active for **verified clubs**. Unverified clubs skip all checks.

### 11.1 Detection Algorithms

| # | Algorithm | Flag Condition |
|---|-----------|---------------|
| 1 | Win Rate Anomaly | Win rate > 85% over 20 matches AND avg opponent rating < player - 200 |
| 2 | Repeated Opponent | Same 2 players matched > 5 times in 7 days AND one always wins |
| 3 | Match Frequency | > 15 matches in 24 hours |
| 4 | Rating Manipulation | Rating drops > 200 in one session, rises > 200 in next |
| 5 | Account Duplication | Two accounts share device/IP AND play against each other |

### 11.2 Risk Scoring

| Factor | Weight |
|--------|--------|
| Win rate anomaly | 30 |
| Repeated opponents | 25 |
| Match frequency | 20 |
| Rating yo-yo | 15 |
| Account similarity | 10 |

**Thresholds:** 0-40 Clean → 41-60 Monitor → 61-80 Flag (notify admins) → 81-100 Auto-restrict

### 11.3 Penalty Levels

| Level | Trigger | Penalty | Duration |
|-------|---------|---------|----------|
| Warning | First flag (61-80) | Notification | — |
| Soft ban | Second flag or > 80 | Matches don't count for rating | 7 days |
| Hard ban | Confirmed manipulation | Rating reset, removed from leaderboard | 30 days |
| Permanent | Repeated offenses | Banned from club | Permanent |

### 11.4 Appeals

Player submits appeal → Club admin reviews → Approves or denies → Super admin can override.

> **Deferred to Phase 4.** Tables (`risk_scores`, `appeals`) not created until needed.

---

## 12. Database Schema

### 12.1 All Tables (13 total)

| # | Table | Purpose |
|---|-------|---------|
| 1 | `users` | User accounts |
| 2 | `clubs` | Club info, settings, payment QR, verification |
| 3 | `club_members` | Membership + role (owner/member) |
| 4 | `club_moderators` | Moderator appointments |
| 5 | `admins` | System-level admins |
| 6 | `sessions` | Play sessions with payment config |
| 7 | `matches` | Individual matches (BO1/BO2/BO3 results) |
| 8 | `player_session_times` | Per-player play minutes (for Type A payment) |
| 9 | `shuttlecock_usage` | Per-player shuttle count per session (for Type B payment) |
| 10 | `inbox_messages` | Notifications & payment requests |
| 11 | `payment_proofs` | Payment slip uploads (30-day expiry) |
| 12 | `pair_requests` | Matchmaking pair requests |
| 13 | `active_pairs` | Active player pairs |

### 12.2 Club Table (Full)

```python
class Club(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    owner_id: int = Field(foreign_key="users.id")
    is_public: bool = Field(default=False)
    logo_url: Optional[str] = None
    created_at: datetime

    # Privacy
    join_password_hash: Optional[str] = None
    invite_code: Optional[str] = Field(default=None, unique=True)
    invite_code_expires_at: Optional[datetime] = None

    # Verification
    is_verified: bool = Field(default=False, index=True)
    verified_by: Optional[int] = Field(foreign_key="users.id")
    verified_at: Optional[datetime] = None
    admin_message: Optional[str] = None

    # Settings
    payment_type: str = Field(default="split")        # "split" | "shuttlecock" | "buffet"
    default_match_type: str = Field(default="single")  # "single" | "bo2" | "bo3"
    shuttlecock_brand: Optional[str] = None
    shuttlecock_model: Optional[str] = None

    # Payment QR
    payment_qr_url: Optional[str] = None
    payment_qr_uploaded_at: Optional[datetime] = None
    payment_method_note: Optional[str] = None

    # Ownership Transfer
    previous_owner_id: Optional[int] = Field(foreign_key="users.id")
    transferred_at: Optional[datetime] = None
```

### 12.3 Session Table

```python
class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id")
    created_by: int = Field(foreign_key="users.id")
    date: date
    start_time: Optional[time] = None
    status: str = Field(default="upcoming")  # upcoming, active, completed
    created_at: datetime

    # Overrides (null = use club default)
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

### 12.4 Match Table

```python
class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    court_id: Optional[int] = None
    team_a_player1_id: int = Field(foreign_key="users.id")
    team_a_player2_id: int = Field(foreign_key="users.id")
    team_b_player1_id: int = Field(foreign_key="users.id")
    team_b_player2_id: int = Field(foreign_key="users.id")
    status: str = Field(default="pending")  # pending, in_progress, completed
    created_at: datetime

    # Match type & set results
    match_type: str = Field(default="single")  # "single" | "bo2" | "bo3"
    set1_winner_team: Optional[str] = None  # "A" or "B"
    set2_winner_team: Optional[str] = None  # BO2/BO3 only
    set3_winner_team: Optional[str] = None  # BO3 only if needed

    # Audit
    result_entered_by: Optional[int] = Field(foreign_key="users.id")
    result_entered_at: Optional[datetime] = None
    result_modified_by: Optional[int] = Field(foreign_key="users.id")
    result_modified_at: Optional[datetime] = None
```

### 12.5 Supporting Tables

```python
class PlayerSessionTime(SQLModel, table=True):
    __tablename__ = "player_session_times"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    play_minutes: int
    entered_by: int = Field(foreign_key="users.id")
    created_at: datetime
    __table_args__ = (UniqueConstraint('session_id', 'player_id'),)

class ShuttlecockUsage(SQLModel, table=True):
    __tablename__ = "shuttlecock_usage"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    quantity: int = Field(default=0)
    entered_by: int = Field(foreign_key="users.id")
    created_at: datetime
    updated_at: Optional[datetime] = None
    __table_args__ = (UniqueConstraint('session_id', 'player_id'),)

class InboxMessage(SQLModel, table=True):
    __tablename__ = "inbox_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str
    message: str
    message_type: str  # "payment", "notification", "invite", "result"
    amount: Optional[Decimal] = None
    qr_code_url: Optional[str] = None
    session_id: Optional[int] = Field(foreign_key="sessions.id")
    is_read: bool = Field(default=False)
    created_at: datetime

class PaymentProof(SQLModel, table=True):
    __tablename__ = "payment_proofs"
    id: Optional[int] = Field(default=None, primary_key=True)
    inbox_message_id: int = Field(foreign_key="inbox_messages.id", index=True)
    player_id: int = Field(foreign_key="users.id", index=True)
    image_url: str
    uploaded_at: datetime
    expires_at: datetime  # uploaded_at + 30 days

class PairRequest(SQLModel, table=True):
    __tablename__ = "pair_requests"
    id: str = Field(primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    requester_id: str = Field(foreign_key="users.id")
    target_id: str = Field(foreign_key="users.id")
    status: str  # PENDING, ACCEPTED, REJECTED, CANCELLED
    message: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    expires_at: datetime  # 7 days
    __table_args__ = (UniqueConstraint('requester_id', 'target_id', 'club_id'),)

class ActivePair(SQLModel, table=True):
    __tablename__ = "active_pairs"
    id: str = Field(primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    player_a_id: str = Field(foreign_key="users.id")  # lower UUID
    player_b_id: str = Field(foreign_key="users.id")  # higher UUID
    created_from_request_id: str = Field(foreign_key="pair_requests.id")
    is_active: bool = Field(default=True)
    created_at: datetime
    __table_args__ = (UniqueConstraint('player_a_id', 'player_b_id', 'club_id'),)
```

---

## 13. API Endpoints

### 13.1 Complete Endpoint List (~45 total)

#### Auth (3)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/auth/register` | None |
| POST | `/auth/login` | None |
| GET | `/auth/me` | Authenticated |

#### Clubs (6)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/clubs` | Authenticated |
| GET | `/clubs` | Authenticated |
| GET | `/clubs/{id}` | Club member |
| PATCH | `/clubs/{id}` | Owner / Moderator |
| DELETE | `/clubs/{id}` | Owner / Admin |
| POST | `/clubs/{id}/transfer-ownership` | Owner / Super Admin |

#### Club Members (3)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/clubs/{id}/members` | Club member |
| PATCH | `/clubs/{id}/members/{uid}/role` | Owner |
| DELETE | `/clubs/{id}/members/{uid}` | Owner / Admin |

#### Club Moderators (3)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/clubs/{id}/moderators` | Owner / Super Admin |
| DELETE | `/clubs/{id}/moderators/{uid}` | Owner / Super Admin |
| GET | `/clubs/{id}/moderators` | Club member |

#### Club Logo & Payment QR (5)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/clubs/{id}/logo` | Owner / Moderator |
| DELETE | `/clubs/{id}/logo` | Owner / Moderator |
| POST | `/clubs/{id}/payment-qr` | Owner / Moderator |
| DELETE | `/clubs/{id}/payment-qr` | Owner / Moderator |
| GET | `/clubs/{id}/payment-qr` | Club member |

#### Privacy & Invites (3)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/clubs/{id}/invite-code` | Owner / Moderator |
| POST | `/clubs/join-by-code` | Authenticated |
| POST | `/clubs/{id}/join-by-password` | Authenticated |

#### Club Search (1)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/clubs/search?q=&page=&limit=` | None (public clubs only) |

#### Sessions (5)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/sessions` | Owner / Moderator |
| GET | `/sessions` | Club member |
| GET | `/sessions/{id}` | Club member |
| PATCH | `/sessions/{id}` | Owner / Moderator |
| GET | `/sessions/{id}/players` | Club member |

#### Session Payments (2)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/sessions/{id}/payments` | Owner / Moderator |
| POST | `/sessions/{id}/payments/send` | Owner / Moderator |

#### Player Time & Shuttlecocks (2 batch endpoints)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/sessions/{id}/player-times` | Owner / Moderator |
| POST | `/sessions/{id}/shuttlecocks` | Owner / Moderator |

#### Matches (2)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/matches/{id}/results` | Player in match / Owner / Moderator |
| PUT | `/matches/{id}/results` | Owner / Moderator only |

#### Inbox (5)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/inbox` | Authenticated (own only) |
| GET | `/inbox/unread-count` | Authenticated |
| PATCH | `/inbox/{id}/read` | Message owner |
| PATCH | `/inbox/read-all` | Authenticated |
| DELETE | `/inbox/{id}` | Message owner |

#### Payment Proofs (2)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/inbox/{id}/proof` | Message owner |
| GET | `/inbox/{id}/proof` | Message owner / Club owner / Moderator |

#### Admin (3)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/admin/clubs/{id}/verify` | Admin / Super Admin |
| POST | `/admin/clubs/{id}/unverify` | Admin / Super Admin |
| GET | `/admin/clubs/pending-verification` | Admin / Super Admin |

#### Matchmaking Pairs (5)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/clubs/{id}/pairs/request` | Club member |
| GET | `/clubs/{id}/pairs/requests` | Club member (own) |
| POST | `/clubs/{id}/pairs/requests/{rid}/accept` | Request target |
| POST | `/clubs/{id}/pairs/requests/{rid}/reject` | Request target |
| GET | `/clubs/{id}/pairs` | Club member (own) |
| DELETE | `/clubs/{id}/pairs/{pid}` | Either player |

---

## 14. Frontend UI

### 14.1 Key Pages

| Page | Path | Description |
|------|------|-------------|
| Club Settings | `/clubs/[id]/settings` | Name, logo, privacy, payment type, match type, QR upload, transfer ownership, admin message |
| Session Create | `/clubs/[id]/sessions/create` | Date, time, court, payment/match overrides, payment-specific fields |
| Match In Progress | `/sessions/[id]/matches/[mid]` | Teams, timer, shuttlecock counter, set result entry |
| Payment Summary | `/sessions/[id]/payments` | Per-player breakdown table with proof status |
| Inbox | `/inbox` | Filtered message list (payment/notification/invite/result) |
| Payment Detail | `/inbox/[id]` | Amount, QR code, upload slip button |
| Admin Panel | `/admin` | Pending verification, club management |

### 14.2 Key UI Components

- `MemberRoleManager` — role assignment dropdown
- `AdminPanel` — super admin dashboard
- Role badges throughout UI (Owner, Moderator, Verified)
- Payment summary table with export (PDF/Excel)

### 14.3 UX Principles

- **Fewer clicks for common tasks, mobile-first**
- Session end → auto-prompt "Calculate payments?"
- Batch entry for shuttlecocks and play times (not per-match)
- Simple minutes input for play time (not time pickers)

---

## 15. Infrastructure

### 15.1 Render Disk

```yaml
# render.yaml
services:
  - type: web
    name: badminton-api
    runtime: python
    plan: starter  # $7/mo — required for disk
    disk:
      name: uploads
      mountPath: /var/data/uploads
      sizeGB: 1
    envVars:
      - key: UPLOAD_DIR
        value: /var/data/uploads
```

**Size estimate:** 100 clubs × 20KB logos = 2MB + originals ~200MB + buffer = **1 GB sufficient**

### 15.2 Static File Serving

```python
# backend/app/main.py
app.mount("/uploads", StaticFiles(directory="/var/data/uploads"), name="uploads")
```

Add `Cache-Control: public, max-age=86400` for upload files.

### 15.3 Backup

- Render disks are persistent but NOT auto-backed up
- Weekly: tar → upload to S3/Cloudflare R2 → keep 4 weeks
- Alternative: Store uploads in S3/R2 from the start

---

## 16. Implementation Plan

### Phase 1: Bug Fixes ✅ (1-2 days)

- [x] Fix club creation race condition (add `await db.commit()`)
- [x] Fix phantom match history (remove mock data)

### Phase 2: Core Structure (1-2 weeks)

| # | Task | Complexity |
|---|------|-----------|
| 1 | DB schema updates (Club, Session, Match new fields) | Medium |
| 2 | ClubModerator table + CRUD | Easy |
| 3 | Admin table + CRUD | Easy |
| 4 | Permission utility refactor | Medium |
| 5 | Verified club system | Easy |
| 6 | Club settings update API | Easy |
| 7 | Frontend: Club settings page | Medium |

### Phase 3: Match & Payment (2-3 weeks)

| # | Task | Complexity |
|---|------|-----------|
| 8 | Match types (BO2/BO3) — model + API | Medium |
| 9 | Result entry system | Medium |
| 10 | Shuttlecock tracking (simplified) | Medium |
| 11 | Payment calculation engine (3 types) | Hard |
| 12 | Session creation flow with overrides | Medium |
| 13 | Inbox + payment messages | Medium |
| 14 | QR upload + payment proof system | Medium |
| 15 | Frontend: match results, payments, inbox | Medium |

### Phase 4: Advanced (2-3 weeks)

| # | Task | Complexity |
|---|------|-----------|
| 16 | Ownership transfer | Medium |
| 17 | Matchmaking pairs | Hard |
| 18 | Anti-gaming (verified club gate) | Hard |
| 19 | Admin panel (pending verification) | Medium |
| 20 | Payment export (PDF/Excel) | Medium |

**Total: 5-8 weeks**

---

## 17. Technical Notes

1. **Database migrations:** Use `alembic revision --autogenerate` after model changes
2. **Transaction safety:** For create-then-redirect flows, use explicit `await db.commit()` (don't rely on `get_db()` post-yield commit)
3. **Cache strategy:** Redis pattern-based invalidation. Keys follow `{entity}:{id}:{action}`. Invalidate AFTER commit.
4. **QR code rendering:** Frontend library (`qrcode.react`) — backend provides invite code URL only
5. **WebSocket notifications:** Pair requests trigger real-time notifications via existing socket manager
6. **Thai language:** All user-facing frontend strings in Thai
7. **Rating system:** Stored on User/ClubMember. Anti-gaming analyzes Match table directly.
8. **Render plan:** Starter ($7/mo) minimum for disk support
9. **Payment calculations:** Computed on-demand, not stored. Fresh calculation on each request.
10. **Shuttlecock confirmation:** Simplified to batch entry by moderator (no per-match confirm/remove flow)
11. **All monetary values:** Use `Decimal` (not float)
12. **Payment export:** `openpyxl` for Excel, `reportlab`/`weasyprint` for PDF

---

## 7. Feature: Court Management & Pre-Match System

### 7.1 Overview

This feature adds **dynamic court management** and a **pre-match queuing system** to sessions. Courts can be added/removed mid-session, each court can auto-match independently, and upcoming matches are arranged in advance so players know who they'll play next.

**Key Concepts:**
- **Dynamic Courts** — Add/remove courts during a live session
- **Auto-Matching Per Court** — Each court independently auto-assigns players when a match ends
- **Pre-Match Queue** — Arrange future matches while current ones are still playing (เปิด/ปิดได้)

---

### 7.2 Dynamic Court Management

**Problem:** Courts are currently fixed at session creation. Need ability to add/remove courts mid-session.

**Solution:**
- Session starts with initial court count → creates Court records
- Moderator can ADD courts (e.g., new court becomes available)
- Moderator can REMOVE courts via soft delete (e.g., maintenance)
- Real-time court status tracking: `available`, `occupied`, `maintenance`, `closed`

**Database Model:**

```python
class Court(SQLModel, table=True):
    __tablename__ = "courts"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    court_number: int  # Court #1, #2, #3, etc.
    status: str = Field(default="available")  # "available", "occupied", "maintenance", "closed"

    # Auto-matching
    auto_matching_enabled: bool = Field(default=True)
    current_match_id: Optional[int] = Field(foreign_key="matches.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None  # Soft delete timestamp
```

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sessions/{id}/courts` | Add new court to session |
| `DELETE` | `/api/v1/sessions/{id}/courts/{court_id}` | Remove court (soft delete) |
| `PATCH` | `/api/v1/sessions/{id}/courts/{court_id}/status` | Update court status |
| `PATCH` | `/api/v1/sessions/{id}/courts/{court_id}/auto-match` | Toggle auto-matching |

**Validation:**
- Cannot remove a court if a match is in progress on it
- Court numbers auto-increment within the session

---

### 7.3 Auto-Matching Per Court

Each court can have auto-matching enabled or disabled independently.

**How it works:**
1. Match ends on Court X
2. If `auto_matching_enabled = True` for Court X:
   - System picks next waiting players (or on-deck pre-match)
   - Assigns them to Court X automatically
3. If `auto_matching_enabled = False`:
   - Court stays empty until moderator manually assigns players

**Rules:**
- Moderator toggles per court at any time
- Disabled courts require manual assignment
- Enabled courts fill immediately when available

---

### 7.4 Pre-Match System

**Concept:** Arrange matches IN ADVANCE while current matches are still playing. Can be enabled/disabled by moderator (เปิด/ปิดได้).

**Player State Flow:**
```
Player Registers → Waiting Pool → Pre-Matched → On Deck → Playing on Court
```

**Queue Visibility:**
- **NOW PLAYING** — Currently on courts
- **ON DECK** — Next up, ready to go when a court opens
- **PRE-MATCH (Preview)** — Future matches, visible to players

**Benefits:**
- Players know who they'll play against → can prepare
- Zero downtime between matches
- Smooth, professional session flow

---

### 7.5 Pre-Match Formula

**Variables:**
- `C` = Number of active courts
- `P` = Number of waiting players (not currently playing)
- `M` = Match size (4 for doubles)

**Minimum to enable pre-match:**
```
Total players needed = (C × M) + (M × 2)

Where:
  C × M  = Players to fill all courts
  M × 2  = Buffer for 2 pre-matches ahead (on-deck + preview)

Example (3 courts, doubles):
  (3 × 4) + (4 × 2) = 12 + 8 = 20 players total
  → 12 playing, 4 on deck, 4 in preview
```

**Dynamic check:**
```python
def can_enable_prematch(courts: int, waiting_players: int) -> bool:
    """Pre-match requires at least 8 waiting players (2 matches ahead)."""
    return waiting_players >= 8
```

**Pre-Match Levels:**

| Waiting Players | Level | Description |
|-----------------|-------|-------------|
| 8–11 | Level 1 | 1 match ahead (on deck only) |
| 12–15 | Level 2 | 2 matches ahead |
| 16–19 | Level 3 | 3 matches ahead |
| 20+ | Level 4 | 4+ matches ahead |

---

### 7.6 Player Allocation Algorithm

**Constraints:**
1. Pre-matched players ≠ currently playing players
2. Pre-matched players ≠ on-deck players
3. Each player appears only once in the pre-match queue
4. Avoid repeat opponents where possible

**Algorithm:**
```python
def calculate_prematches(players, courts):
    playing = get_currently_playing()
    on_deck = get_on_deck()
    available = [p for p in players if p not in playing and p not in on_deck]

    matches_ahead = len(available) // 4
    prematches = []

    for i in range(matches_ahead):
        if len(available) >= 4:
            match_players = select_players(available, avoid_recent_opponents=True)
            prematches.append(match_players)
            available = [p for p in available if p not in match_players]

    return prematches
```

---

### 7.7 Database: PreMatch Model

```python
class PreMatch(SQLModel, table=True):
    __tablename__ = "pre_matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")

    match_order: int = Field(default=1)  # 1 = on deck, 2 = preview, 3+ = future

    # Players (doubles = 4)
    team_a_player_1_id: int = Field(foreign_key="users.id")
    team_a_player_2_id: int = Field(foreign_key="users.id")
    team_b_player_1_id: int = Field(foreign_key="users.id")
    team_b_player_2_id: int = Field(foreign_key="users.id")

    status: str = Field(default="queued")  # "queued", "on_deck", "active", "cancelled"
    becomes_active_when: Optional[int] = None  # match_id that triggers promotion

    created_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
```

---

### 7.8 API Endpoints (Complete)

**Court Management:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sessions/{id}/courts` | Add court |
| `DELETE` | `/api/v1/sessions/{id}/courts/{court_id}` | Remove (soft delete) |
| `PATCH` | `/api/v1/sessions/{id}/courts/{court_id}` | Update settings |

**Pre-Match:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sessions/{id}/prematches` | View pre-match queue |
| `POST` | `/api/v1/sessions/{id}/prematches/enable` | Enable (with validation) |
| `POST` | `/api/v1/sessions/{id}/prematches/disable` | Disable |
| `GET` | `/api/v1/sessions/{id}/prematches/status` | Check if can enable |

**Auto-Match:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/courts/{court_id}/auto-match/enable` | Enable auto-match |
| `POST` | `/api/v1/courts/{court_id}/auto-match/disable` | Disable auto-match |

---

### 7.9 UI/UX Mockups

**Court Display Board (Moderator):**
```
┌─────────────────────────────────────┐
│ COURT STATUS          [+ Add Court] │
├─────────────────────────────────────┤
│ Court 1  [OCCUPIED]  [Auto: ON ✓]  │
│   Match: Team A vs Team B           │
│   Time: 00:23:15                    │
├─────────────────────────────────────┤
│ Court 2  [AVAILABLE] [Auto: OFF]    │
│   [Assign Players] [Toggle Auto]    │
├─────────────────────────────────────┤
│ Court 3  [OCCUPIED]  [Auto: ON ✓]  │
│   Match: Team C vs Team D           │
└─────────────────────────────────────┘
```

**Pre-Match Display (Everyone):**
```
┌──────────────────────────────────────┐
│ NEXT MATCHES (Pre-Match Enabled)     │
├──────────────────────────────────────┤
│ NOW PLAYING (3 courts)               │
│ • Court 1: Alice+Bob vs Carol+Dave   │
│ • Court 2: Eve+Frank vs Grace+Henry  │
│ • Court 3: Ivy+Jack vs Kate+Leo      │
├──────────────────────────────────────┤
│ ON DECK (Next)                       │
│ → Match 4: Mike+Nancy vs Oscar+Pam   │
├──────────────────────────────────────┤
│ PRE-MATCH (Preview)                  │
│ • Match 5: Quinn+Rachel vs Sam+Tina  │
│ • Match 6: Uma+Victor vs Wendy+Xavier│
└──────────────────────────────────────┘
```

**Player View:**
```
Your Status:
├─ Current: Playing on Court 1 (vs Carol+Dave)
├─ Next: Pre-matched with Nancy vs Oscar+Pam
└─ Estimated wait: ~15 minutes
```

---

### 7.10 Implementation Phases

| Phase | Scope | Description |
|-------|-------|-------------|
| **Phase 1** | Dynamic Courts | Add/remove courts mid-session, status tracking |
| **Phase 2** | Auto-Matching | Per-court auto-match toggle, automatic player assignment |
| **Phase 3** | Pre-Match System | Queue, validation, on-deck/preview display |
| **Phase 4** | Advanced Algorithms | Avoid repeat opponents, skill-based balancing |

**Validation Rules:**
- Cannot remove court with active match
- Cannot enable pre-match if waiting players < 8
- Pre-matches auto-cancel if a player leaves the session
- Auto-promote pre-match → on-deck when a court becomes available
