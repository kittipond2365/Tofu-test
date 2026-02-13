import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

async def fix():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
        
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        columns = [
            ("invite_code", "VARCHAR"),
            ("invite_qr_url", "VARCHAR"),
            ("payment_qr_url", "VARCHAR"),
            ("payment_method_note", "VARCHAR"),
            ("updated_at", "TIMESTAMP"),
        ]
        for col, type_ in columns:
            result = await conn.execute(text(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='clubs' AND column_name='{col}'
            """))
            if result.scalar() is None:
                print(f"➕ Adding {col}...")
                await conn.execute(text(f"ALTER TABLE clubs ADD COLUMN {col} {type_}"))
            else:
                print(f"✅ {col} already exists")
    await engine.dispose()
    print("✅ Clubs columns fix complete")

if __name__ == "__main__":
    asyncio.run(fix())
