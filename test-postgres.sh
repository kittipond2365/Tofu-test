#!/bin/bash
# Test on PostgreSQL before deploying to Render

set -e

echo "🐳 Starting PostgreSQL + Redis via Docker..."
cd "$(dirname "$0")/.."
docker-compose -f docker-compose.local.yml up -d

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec badminton-postgres pg_isready -U badminton_user -d badminton_db; do
    echo "   Still waiting..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

cd backend
source venv/bin/activate

echo ""
echo "🗄️  Switching to PostgreSQL mode..."
export $(cat .env.postgres | xargs)

echo "🔄 Running database initialization..."
python3 << 'PYEOF'
import asyncio
from app.core.database import init_db

async def setup():
    print("Creating tables...")
    await init_db()
    print("✅ Tables created on PostgreSQL!")

asyncio.run(setup())
PYEOF

echo ""
echo "🧪 Running feature tests..."
python3 << 'PYEOF'
import asyncio
import uuid
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.models import User, Club, Session, Match, ClubMember, SessionRegistration
from sqlalchemy import select

async def test_all_features():
    async with AsyncSessionLocal() as session:
        print("\n📋 Test 1: Create User")
        user = User(
            id=str(uuid.uuid4()),
            line_user_id=f"test_pg_{uuid.uuid4().hex[:8]}",
            display_name="PostgreSQL Test User",
            email="pgtest@example.com"
        )
        session.add(user)
        await session.flush()
        print(f"   ✅ User created: {user.id[:8]}...")
        
        print("\n📋 Test 2: Create Club")
        club = Club(
            id=str(uuid.uuid4()),
            name="PG Test Club",
            slug=f"pg-club-{uuid.uuid4().hex[:6]}",
            description="Testing on PostgreSQL",
            location="Bangkok",
            max_members=50,
            is_public=True,
            owner_id=user.id
        )
        session.add(club)
        await session.flush()
        print(f"   ✅ Club created: {club.name}")
        
        print("\n📋 Test 3: Add Member to Club")
        member = ClubMember(
            club_id=club.id,
            user_id=user.id,
            role="owner"
        )
        session.add(member)
        print(f"   ✅ Member added")
        
        print("\n📋 Test 4: Create Session")
        sess = Session(
            id=str(uuid.uuid4()),
            club_id=club.id,
            title="Friday Session",
            description="Weekly badminton",
            location="Sports Complex",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=3),
            number_of_courts=3,
            max_participants=20,
            payment_type="split",
            status="upcoming",
            created_by=user.id
        )
        session.add(sess)
        await session.flush()
        print(f"   ✅ Session created: {sess.title}")
        
        print("\n📋 Test 5: Register for Session")
        reg = SessionRegistration(
            session_id=sess.id,
            user_id=user.id,
            status="confirmed"
        )
        session.add(reg)
        print(f"   ✅ Registered")
        
        print("\n📋 Test 6: Create Match (Matchmaking)")
        # Create 3 more players
        players = [user]
        for i in range(3):
            p = User(
                id=str(uuid.uuid4()),
                line_user_id=f"player{i}_{uuid.uuid4().hex[:6]}",
                display_name=f"Player {i+1}",
                email=f"p{i}@example.com"
            )
            session.add(p)
            await session.flush()
            players.append(p)
        
        match = Match(
            id=str(uuid.uuid4()),
            session_id=sess.id,
            court_number=1,
            match_type="doubles",
            team_a_player_1_id=players[0].id,
            team_a_player_2_id=players[1].id,
            team_b_player_1_id=players[2].id,
            team_b_player_2_id=players[3].id,
            status="scheduled",
            created_at=datetime.now()
        )
        session.add(match)
        print(f"   ✅ Match created: {players[0].display_name} & {players[1].display_name} vs {players[2].display_name} & {players[3].display_name}")
        
        await session.commit()
        
        print("\n📋 Test 7: Query Data")
        result = await session.execute(select(Club))
        clubs = result.scalars().all()
        print(f"   ✅ Found {len(clubs)} club(s)")
        
        result = await session.execute(select(Match))
        matches = result.scalars().all()
        print(f"   ✅ Found {len(matches)} match(es)")
        
        return True

try:
    success = asyncio.run(test_all_features())
    if success:
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED ON POSTGRESQL!")
        print("="*50)
        print("\n✅ ระบบพร้อม deploy บน Render (PostgreSQL)")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

echo ""
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.local.yml down

echo ""
echo "✅ PostgreSQL testing complete!"
