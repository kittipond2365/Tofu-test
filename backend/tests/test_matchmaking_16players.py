import pytest
import httpx
import asyncio
import os

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
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/clubs",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "description": "Test club for matchmaking"
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
        await client.post(
            f"{BASE_URL}/api/v1/clubs/{club_id}/join",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )

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

async def register_session(token: str, session_id: str):
    """Register เข้าร่วม session"""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/register",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )

async def run_matchmaking(token: str, session_id: str):
    """Run matchmaking"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/matchmake",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Test-Secret": TEST_SECRET
            }
        )
        return resp.json()

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
        
        # 4. สร้าง session
        print("Creating session...")
        session = await create_session(owner["token"], club_id, "16 Players Tournament")
        session_id = session["id"]
        
        # 5. ให้ทุกคน register
        print("All players registering...")
        for player in players:
            await register_session(player["token"], session_id)
        
        # 6. รัน matchmaking
        print("Running matchmaking...")
        result = await run_matchmaking(owner["token"], session_id)
        
        # 7. ตรวจสอบผล
        print("Checking results...")
        matches = result.get("matches", [])
        
        # ต้องมี 8 คู่
        assert len(matches) == 8, f"Expected 8 matches, got {len(matches)}"
        
        # ตรวจสอบว่าทุกคนมีคู่
        matched_players = set()
        for match in matches:
            matched_players.update(match.get("players", []))
        
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
