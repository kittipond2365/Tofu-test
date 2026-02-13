"""Direct database migration using SQLModel - Fallback when Alembic fails"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")

async def migrate():
    print(f"🔄 Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        print("🔍 Checking database columns...")
        
        # ========== USERS TABLE ==========
        # Check and add picture_url
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'picture_url'
        """))
        if result.scalar() is None:
            print("➕ Adding picture_url to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN picture_url VARCHAR"))
        else:
            print("✓ picture_url already exists")
        
        # Check and add email
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'email'
        """))
        if result.scalar() is None:
            print("➕ Adding email to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
        else:
            print("✓ email already exists")
        
        # Check and add phone
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'phone'
        """))
        if result.scalar() is None:
            print("➕ Adding phone to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR"))
        else:
            print("✓ phone already exists")
        
        # Check and add is_super_admin
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_super_admin'
        """))
        if result.scalar() is None:
            print("➕ Adding is_super_admin to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE"))
        else:
            print("✓ is_super_admin already exists")
        
        # Check and add updated_at
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """))
        if result.scalar() is None:
            print("➕ Adding updated_at to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP"))
        else:
            print("✓ updated_at already exists")
        
        # ========== CLUBS TABLE ==========
        # Check and add owner_id
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clubs' AND column_name = 'owner_id'
        """))
        if result.scalar() is None:
            print("➕ Adding owner_id to clubs...")
            await conn.execute(text("ALTER TABLE clubs ADD COLUMN owner_id VARCHAR(36)"))
        else:
            print("✓ owner_id already exists")
        
        # Check and add is_verified
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clubs' AND column_name = 'is_verified'
        """))
        if result.scalar() is None:
            print("➕ Adding is_verified to clubs...")
            await conn.execute(text("ALTER TABLE clubs ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
        else:
            print("✓ is_verified already exists")
        
        # Check and add payment_qr_url
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clubs' AND column_name = 'payment_qr_url'
        """))
        if result.scalar() is None:
            print("➕ Adding payment_qr_url to clubs...")
            await conn.execute(text("ALTER TABLE clubs ADD COLUMN payment_qr_url VARCHAR"))
        else:
            print("✓ payment_qr_url already exists")
        
        print("✅ Migration complete!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
