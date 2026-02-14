#!/bin/bash
# Diagnostic script for Render deployment

echo "🔍 Checking Render Deployment..."
echo "================================"

# Check if required env vars are set
echo ""
echo "📋 Checking Environment Variables:"

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
else
    echo "✅ DATABASE_URL is set"
    # Mask password
    echo "   URL: ${DATABASE_URL%%:*}://***@${DATABASE_URL#*@}"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY not set"
else
    echo "✅ SECRET_KEY is set (${#SECRET_KEY} chars)"
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL not set"
else
    echo "✅ REDIS_URL is set"
    echo "   URL: ${REDIS_URL%%:*}://***@${REDIS_URL#*@}"
fi

echo ""
echo "🧪 Testing Connections:"

# Test PostgreSQL connection
echo "   Testing PostgreSQL..."
python3 << 'PYEOF'
import asyncio
import os
import sys

async def test_db():
    try:
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            print("   ❌ DATABASE_URL not set")
            return False
            
        # Normalize URL for asyncpg
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        print(f"   Connecting to: {database_url.split('@')[1].split('/')[0]}...")
        
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.scalar()
        await engine.dispose()
        
        print("   ✅ PostgreSQL connection OK")
        return True
    except Exception as e:
        print(f"   ❌ PostgreSQL failed: {e}")
        return False

result = asyncio.run(test_db())
sys.exit(0 if result else 1)
PYEOF

# Test Redis connection
echo ""
echo "   Testing Redis..."
python3 << 'PYEOF'
import asyncio
import os
import sys

async def test_redis():
    try:
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            print("   ❌ REDIS_URL not set")
            return False
        
        print(f"   Connecting to: {redis_url.split('@')[1].split(':')[0]}...")
        
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await r.ping()
        await r.close()
        
        print("   ✅ Redis connection OK")
        return True
    except Exception as e:
        print(f"   ❌ Redis failed: {e}")
        return False

result = asyncio.run(test_redis())
sys.exit(0 if result else 1)
PYEOF

echo ""
echo "================================"
echo "🔧 Recommendations:"
echo ""
echo "If PostgreSQL fails:"
echo "   1. Check DATABASE_URL format"
echo "   2. Verify Supabase project is active"
echo "   3. Check if password is correct"
echo ""
echo "If Redis fails:"
echo "   1. Check REDIS_URL format"
echo "   2. For Upstash, ensure you're using rediss:// (SSL)"
echo "   3. Try redis:// instead of rediss:// if SSL issues"
echo ""
echo "To run diagnostics on Render:"
echo "   1. Go to Render Dashboard → your service → Shell"
echo "   2. Run: python3 -c \"import os; print(os.getenv('DATABASE_URL'))\""
echo "   3. Run: python3 -c \"import os; print(os.getenv('REDIS_URL'))\""
