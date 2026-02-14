#!/bin/bash
# Debug Network & Database Connection on Render

echo "🔍 Render Deployment Debug"
echo "=========================="

# Test DNS resolution
echo ""
echo "1. Testing DNS resolution..."
python3 << 'PYEOF'
import socket
import sys

hosts = [
    "db.bmxyluncwluldoecwjkk.supabase.co",
    "google.com",
    "api.render.com"
]

for host in hosts:
    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ {host} -> {ip}")
    except Exception as e:
        print(f"   ❌ {host} -> {e}")
PYEOF

# Test internet connectivity
echo ""
echo "2. Testing internet connectivity..."
curl -s -o /dev/null -w "%{http_code}" https://google.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Can reach internet"
else
    echo "   ❌ Cannot reach internet"
fi

# Test Supabase connection
echo ""
echo "3. Testing Supabase PostgreSQL..."
python3 << 'PYEOF'
import os
import sys

database_url = os.getenv("DATABASE_URL", "")
if not database_url:
    print("   ❌ DATABASE_URL not set")
    sys.exit(1)

# Extract hostname
host = database_url.split('@')[1].split(':')[0] if '@' in database_url else "unknown"
print(f"   Host: {host}")

# Try to resolve
import socket
try:
    ip = socket.gethostbyname(host)
    print(f"   ✅ DNS resolved: {ip}")
except Exception as e:
    print(f"   ❌ DNS failed: {e}")
    sys.exit(1)

# Try to connect to port 5432
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
try:
    result = sock.connect_ex((ip, 5432))
    if result == 0:
        print(f"   ✅ Port 5432 is open")
    else:
        print(f"   ❌ Port 5432 is closed or blocked (error: {result})")
except Exception as e:
    print(f"   ❌ Connection test failed: {e}")
finally:
    sock.close()
PYEOF

# Test actual database connection
echo ""
echo "4. Testing database connection..."
python3 << 'PYEOF'
import asyncio
import os
import sys

async def test():
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("   ❌ DATABASE_URL not set")
        return False
    
    try:
        # Normalize URL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.scalar()
        await engine.dispose()
        
        print("   ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
PYEOF

echo ""
echo "=========================="
echo "🔧 If DNS fails:"
echo "   - Check if Supabase project is paused (free tier pauses after 7 days)"
echo "   - Try using Supabase IPv4 address directly"
echo ""
echo "🔧 If port is blocked:"
echo "   - Supabase may block Render IP"
echo "   - Try using Supabase connection pooling (port 6543)"
echo ""
echo "🔧 Alternative: Use Supabase Session Pooler"
echo "   URL format: postgresql://postgres.xxx:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6542/postgres"
