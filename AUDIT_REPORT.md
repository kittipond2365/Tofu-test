# Usability Audit Report — Badminton Club App

**Date:** 2026-02-14  
**Auditor:** AI UX Audit  

---

## Executive Summary

The app has a solid backend with most core APIs implemented (join club, register for session, open session, check-in/out, auto-matchmaking, score tracking). However, **the frontend is severely disconnected from the backend** — many working API endpoints have no corresponding UI buttons or pages. The result: users hit dead ends constantly.

**Backend completeness: ~75%** | **Frontend completeness: ~35%** | **User can complete core flow: NO**

The #1 blocker is that users cannot transition a session from DRAFT → OPEN in the UI, which means no one can register, which means no matches can happen.

---

## Critical Gap: Backend APIs Without Frontend UI

| Feature | Backend API | Frontend UI | Gap |
|---------|------------|-------------|-----|
| Join club | `POST /clubs/{id}/join` ✅ | `/clubs/join` page exists ✅ | **But no "Join" button on club detail page** |
| Open session | `POST /sessions/{id}/open` ✅ | `apiClient.openRegistration()` exists | **No button anywhere calls it** |
| Register for session | `POST /sessions/{id}/register` ✅ | Session detail has Register button ✅ | Works IF session is OPEN (but can't open it) |
| Cancel registration | `POST /sessions/{id}/cancel` ✅ | Session detail has Cancel button ✅ | Works |
| Check-in | `POST /sessions/{id}/checkin` ✅ | Session detail has Check-in button ✅ | Works |
| Check-out | `POST /sessions/{id}/checkout` ✅ | Session detail has Check-out button ✅ | Works |
| Auto-matchmaking | `POST /sessions/{id}/matches` ✅ | Session detail has Create Match button ✅ | Works |
| View registrations | `GET /sessions/{id}/registrations` ✅ | Session detail shows list ✅ | Works |
| Score update | `PATCH /matches/{id}/score` ✅ | Unknown | Need to check MatchCard |
| Leave club | ❌ | ❌ | Not implemented |
| Payment | ❌ | ❌ | Not implemented |

---

## Critical Missing Features (Must-Have for MVP)

### Priority 1 — Flow Blockers (Users literally cannot use the app)

1. **"Open Registration" button on session detail page**  
   - Backend: `POST /sessions/{id}/open` ✅ ready  
   - Frontend: `apiClient.openRegistration()` ✅ ready  
   - **Missing:** A button in the session detail page (for admin/organizer) that calls it  
   - **Fix:** Add button in session detail when `session.status === 'draft'` — estimated 15 min

2. **"Join Club" button on club detail page**  
   - Backend: `POST /clubs/{id}/join` ✅ ready  
   - Frontend: `apiClient.joinClub()` ✅ ready  
   - **Missing:** The club detail page (`/clubs/[clubId]`) requires membership to view (403). Non-members can't see the page to join it.  
   - **Fix:** Backend needs a public club view endpoint OR a join-by-slug flow. The `/clubs/join` page exists but requires knowing the slug. Add a "Browse Public Clubs" page.

3. **Club discovery for non-members**  
   - `GET /clubs` only returns clubs where user is member  
   - No way to discover or browse public clubs  
   - **Fix:** Add `GET /clubs/public` endpoint + browse page

### Priority 2 — Core Features Still Missing

4. **Leave club** — No API or UI
5. **Session status management** — No UI for Close/Cancel session (backend has delete but not close/cancel status transitions)
6. **Payment/cost splitting** — No API or UI at all
7. **Member role management** — No UI to change member roles

---

## Quick Wins (< 1 hour each, high impact)

### 1. Add "เปิดรับสมัคร" (Open Registration) Button — 15 min
In `/clubs/[clubId]/sessions/[sessionId]/page.tsx`, add after the status banner:

```tsx
// Add mutation
const openMutation = useMutation({
  mutationFn: () => apiClient.openRegistration(params.sessionId),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['session', params.sessionId] })
});

// Add button when status is draft
{session.status === 'draft' && (
  <button onClick={() => openMutation.mutate()} className="btn-primary w-full">
    เปิดรับสมัคร
  </button>
)}
```

### 2. Fix Session List Status Filter — 5 min
The filter options don't include `draft`. Add:
```tsx
{ value: 'draft', label: 'ร่าง' },
```

### 3. Add "Join" Button to Club Detail Page — 30 min
The club detail page is currently members-only. Two options:
- **Quick:** Make `/clubs/join` page more discoverable (add link from clubs list page)
- **Better:** Add public club view endpoint that shows club info + join button

### 4. Fix Timezone Display — 10 min
Sessions already use `toLocaleDateString('th-TH')` which should display correctly in Bangkok timezone. The `-07:00` offset issue is likely from storing naive datetimes. The `make_naive()` in session creation strips timezone info, but the frontend `new Date()` constructor may misinterpret it. Fix: ensure backend returns ISO strings with `+07:00` or `Z` suffix.

### 5. Add "Browse Clubs" Link — 5 min
On `/clubs` page, add a prominent link to `/clubs/join`.

---

## Recommended User Flows

### New User Journey (Current vs. Ideal)

**Current (BROKEN):**
1. Land on homepage → Login with LINE ✅
2. See clubs list (empty) ✅
3. ??? No way to find clubs → DEAD END

**Ideal:**
1. Land on homepage → Login with LINE
2. See "My Clubs" (empty) + **"Browse Public Clubs"** button
3. Browse clubs → Click one → See club info + **"Join"** button
4. After joining → See club detail with sessions
5. Click session → **Register** button (if session is OPEN)

### Club Owner Journey (Current vs. Ideal)

**Current (BROKEN):**
1. Create club ✅
2. Create session ✅ (status: DRAFT)
3. ??? No way to open session → DEAD END

**Ideal:**
1. Create club → Auto-redirected to club detail
2. Create session → Status: DRAFT
3. Click session → Click **"เปิดรับสมัคร"** → Status: OPEN
4. Members register → See participant list
5. On match day → Click **"สร้างแมทช์"** → Auto-matchmaking
6. Record scores → Session complete

### Club Member Journey

**Current (BROKEN):**
1. Need to know club slug → Go to `/clubs/join` → Enter slug
2. If they find a session, it's stuck in DRAFT → Can't register

**Ideal:**
1. Browse clubs OR enter invite code/slug
2. Join club → See upcoming sessions
3. Register for session → Get confirmation
4. On match day → Check-in → Play matches → Check-out

---

## UX Issues

### 1. Dead-End States
- **Empty clubs page** — No guidance on what to do next
- **DRAFT session** — No action to open it, no explanation
- **Sessions tab on club detail** — Just shows a "View All" button, doesn't inline sessions

### 2. Missing Feedback
- No toast/notification after creating a session
- No confirmation dialog before canceling registration
- No loading states on some mutations

### 3. Navigation Issues
- `/clubs/join` is hard to discover (no link from main clubs page)
- Session detail breadcrumbs work well ✅
- Club detail breadcrumbs work well ✅
- No "My upcoming sessions" across all clubs

### 4. Role Visibility
- Admin/Organizer don't see different UI than regular members
- "Create Session" button shows for everyone on club detail (should only show for admin/organizer)
- No visual indicator of user's role in the club

### 5. Timezone
- Backend strips timezone with `make_naive()` then stores in PostgreSQL
- No timezone context sent to frontend
- Should store as UTC and convert on display, OR store with timezone

---

## Testing Checklist

### Authentication
- [ ] LINE Login → redirect → token stored
- [ ] Token refresh works on 401
- [ ] Logout clears state

### Club Management
- [ ] Create club with valid data
- [ ] Create club with duplicate slug → error
- [ ] View club detail (as member)
- [ ] View club detail (as non-member) → currently 403, needs fix
- [ ] Join public club via `/clubs/join`
- [ ] Join club that's full → error

### Session Management  
- [ ] Create session with valid data
- [ ] Create session with end_time before start_time → error
- [ ] **Open session (DRAFT → OPEN)** — NEEDS UI BUTTON
- [ ] View session detail
- [ ] View session list with filters
- [ ] Calendar view shows sessions on correct days

### Registration
- [ ] Register for OPEN session
- [ ] Register when session is FULL → waitlisted
- [ ] Cancel registration → promoted from waitlist
- [ ] Check-in
- [ ] Check-out

### Matches
- [ ] Auto-create match (needs ≥4 registered players)
- [ ] Start match
- [ ] Update score
- [ ] Complete match → ratings updated
- [ ] View match history

### Edge Cases
- [ ] Session with 0 registrations → create match should fail gracefully
- [ ] Double registration → proper error
- [ ] Timezone: sessions display correct Bangkok time
- [ ] Mobile responsiveness of all pages

---

## Implementation Priority

| # | Task | Effort | Impact | Priority |
|---|------|--------|--------|----------|
| 1 | Add "Open Registration" button | 15 min | CRITICAL | 🔴 P0 |
| 2 | Add public clubs browse | 2 hrs | CRITICAL | 🔴 P0 |
| 3 | Add "Join" on club detail (public view) | 2 hrs | CRITICAL | 🔴 P0 |
| 4 | Add "draft" to session filter | 5 min | HIGH | 🟡 P1 |
| 5 | Add "Browse Clubs" link on clubs page | 5 min | HIGH | 🟡 P1 |
| 6 | Role-based UI (hide admin buttons) | 1 hr | MEDIUM | 🟡 P1 |
| 7 | Fix timezone handling | 1 hr | MEDIUM | 🟡 P1 |
| 8 | Leave club API + UI | 1 hr | LOW | 🟢 P2 |
| 9 | Payment/cost splitting | 1 day | LOW (MVP) | 🟢 P2 |
| 10 | Cross-club "My Sessions" dashboard | 2 hrs | NICE | 🔵 P3 |

**Bottom line:** The app is ~70% built but 0% usable. Three UI buttons (Open Registration, Join Club, Browse Clubs) would unlock the entire flow. Start there.
