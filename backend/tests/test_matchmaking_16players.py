import pytest
import httpx
import asyncio
import os
import uuid

BASE_URL = os.getenv("TEST_API_URL", os.getenv("TEST_TARGET_URL", "https://tofubadminton-backend.onrender.com"))
TEST_SECRET = os.getenv("TEST_SECRET", "test-secret-for-ci-only-2024")

# Track สร้างอะไรบ้างเพื่อ cleanup
created_clubs = []
created_sessions = []
created_users = []

async def create_test_user(name: str):
    """สร้าง test user และ return token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/test-login",
            json={"name": name},
            headers={"X-Test-Secret": TEST_SECRET}
        )
        data = resp.json()
        created_users.append(data["user"]["id"])
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "name": name
        }

async def create_test_club(token: str, name: str):
    """สร้าง test club"""
    # สร้าง unique slug ด้วย uuid
    unique_suffix = str(uuid.uuid4())[:8]
    slug = f"{name.lower().replace(' ', '-')}-{unique_suffix}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/clubs",
            json={
                "name": name,
                "slug": slug,
                "description": "Test club for matchmaking",
                "is_public": True
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        club = resp.json()
        if resp.status_code != 201:
            pytest.fail(f"Failed to create club: {resp.status_code} - {club}")
        created_clubs.append(club["id"])
        return club

async def join_club(token: str, club_id: str):
    """ให้ user join club"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/clubs/{club_id}/join",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        if resp.status_code not in [200, 201]:
            print(f"  Join club failed: {resp.status_code} - {resp.text}")
        return resp.json()

async def create_session(token: str, club_id: str, title: str):
    """สร้าง session"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/clubs/{club_id}/sessions",
            json={
                "title": title,
                "start_time": "2026-02-20T18:00:00",
                "max_participants": 16
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        session = resp.json()
        created_sessions.append(session["id"])
        return session

async def open_session(token: str, session_id: str):
    """เปิด session สำหรับ registration"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/open",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        if resp.status_code != 200:
            print(f"  Open session failed: {resp.status_code} - {resp.text}")
        return resp.json()

async def register_session(token: str, session_id: str):
    """Register เข้าร่วม session"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/register",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        if resp.status_code != 200:
            print(f"  Registration failed: {resp.status_code} - {resp.text}")
        return resp.json()

async def run_matchmaking_once(token: str, session_id: str):
    """Run matchmaking once - creates one doubles match with auto-matchmaking"""
    async with httpx.AsyncClient() as client:
        # Call the matches endpoint with empty body to trigger auto-matchmaking
        resp = await client.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/matches",
            json={},  # Empty body triggers auto-matchmaking
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        if resp.status_code != 201:
            print(f"Matchmaking failed: {resp.status_code} - {resp.text}")
            return None
        return resp.json()

async def get_all_matches(token: str, session_id: str):
    """Get all matches for a session"""
    async with httpx.AsyncClient() as client:
        matches_resp = await client.get(
            f"{BASE_URL}/api/v1/sessions/{session_id}/matches",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        return matches_resp.json()

async def cleanup():
    """ลบทุกอย่างที่สร้าง"""
    async with httpx.AsyncClient() as client:
        # ลบ sessions
        for session_id in created_sessions:
            try:
                await client.delete(
                    f"{BASE_URL}/api/v1/sessions/{session_id}",
                    headers={"X-Test-Secret": TEST_SECRET}
                )
            except:
                pass
        
        # ลบ clubs
        for club_id in created_clubs:
            try:
                await client.delete(
                    f"{BASE_URL}/api/v1/clubs/{club_id}",
                    headers={"X-Test-Secret": TEST_SECRET}
                )
            except:
                pass

@pytest.mark.asyncio
async def test_matchmaking_16_players_fair():
    """Test matchmaking with 16 players - fairness check"""
    try:
        # 1. สร้าง test users 16 คน
        print("Creating 16 test users...")
        players = []
        for i in range(1, 17):
            player = await create_test_user(f"MatchTest Player {i}")
            players.append(player)
        
        # 2. สร้าง club (โดย player 1)
        print("Creating club...")
        owner = players[0]
        club = await create_test_club(owner["token"], "Fair Matchmaking Test Club")
        club_id = club["id"]
        
        # 3. ให้ทุกคน join club
        print("All players joining club...")
        for player in players:
            await join_club(player["token"], club_id)
        
        # 4. สร้าง session และเปิด registration
        print("Creating session...")
        session = await create_session(owner["token"], club_id, "16 Players Tournament")
        session_id = session["id"]
        
        print("Opening session for registration...")
        await open_session(owner["token"], session_id)
        
        # 5. ให้ทุกคน register
        print("All players registering...")
        for player in players:
            await register_session(player["token"], session_id)
        
        # 6. รัน matchmaking 4 ครั้ง (สร้าง 4 คู่สำหรับ 16 คน)
        print("Running matchmaking...")
        for i in range(4):
            match = await run_matchmaking_once(owner["token"], session_id)
            if match:
                print(f"  Created match {i+1}: Court {match.get('court_number')}")
        
        # 7. ตรวจสอบผล
        print("Checking results...")
        matches = await get_all_matches(owner["token"], session_id)
        
        # ต้องมี 4 คู่ (แบดมินตันคู่ = 4 คนต่อคู่, 16 คน = 4 คู่)
        assert len(matches) == 4, f"Expected 4 matches, got {len(matches)}"
        
        # ตรวจสอบว่าทุกคนมีคู่
        matched_players = set()
        for match in matches:
            matched_players.add(match["team_a_player_1"]["id"])
            matched_players.add(match["team_b_player_1"]["id"])
            if match.get("team_a_player_2"):
                matched_players.add(match["team_a_player_2"]["id"])
            if match.get("team_b_player_2"):
                matched_players.add(match["team_b_player_2"]["id"])
        
        assert len(matched_players) == 16, f"Expected 16 matched players, got {len(matched_players)}"
        
        # ตรวจสอบ fairness (ถ้ามี skill level)
        # ... (เพิ่มตรวจสอบ skill-based matching ถ้ามี)
        
        print("✅ Matchmaking test passed!")
        
    finally:
        # Cleanup
        print("Cleaning up...")
        await cleanup()

# Run test
if __name__ == "__main__":
    asyncio.run(test_matchmaking_16_players_fair())
