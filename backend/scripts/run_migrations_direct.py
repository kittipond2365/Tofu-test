"""Complete database migration - adds ALL missing columns"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")

# Normalize URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:

        # Helper to check column existence
        async def column_exists(table, column):
            result = await conn.execute(text(f"""
                SELECT 1 FROM information_schema.columns
                WHERE table_name='{table}' AND column_name='{column}'
            """))
            return result.scalar() is not None

        # ========== USERS TABLE ==========
        user_columns = [
            ("picture_url", "VARCHAR"),
            ("email", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("is_super_admin", "BOOLEAN DEFAULT FALSE"),
            ("updated_at", "TIMESTAMP"),
            ("full_name", "VARCHAR"),
            ("hashed_password", "VARCHAR"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("rating", "FLOAT DEFAULT 1000.0"),
            ("total_matches", "INTEGER DEFAULT 0"),
            ("wins", "INTEGER DEFAULT 0"),
            ("losses", "INTEGER DEFAULT 0"),
            ("fcm_token", "VARCHAR"),
        ]

        for col, type_ in user_columns:
            if not await column_exists("users", col):
                print(f"➕ Adding users.{col}")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {type_}"))

        # ========== CLUBS TABLE ==========
        club_columns = [
            ("owner_id", "VARCHAR REFERENCES users(id)"),
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("verified_by", "VARCHAR REFERENCES users(id)"),
            ("verified_at", "TIMESTAMP"),
            ("previous_owner_id", "VARCHAR REFERENCES users(id)"),
            ("transferred_at", "TIMESTAMP"),
            ("invite_code", "VARCHAR"),
            ("invite_qr_url", "VARCHAR"),
            ("payment_qr_url", "VARCHAR"),
            ("payment_method_note", "VARCHAR"),
            ("updated_at", "TIMESTAMP"),
        ]

        for col, type_ in club_columns:
            if not await column_exists("clubs", col):
                print(f"➕ Adding clubs.{col}")
                await conn.execute(text(f"ALTER TABLE clubs ADD COLUMN {col} {type_}"))

        # ========== CLUB_MEMBERS TABLE ==========
        club_member_columns = [
            ("id", "SERIAL PRIMARY KEY"),  # This is tricky - need to handle carefully
            ("role", "VARCHAR DEFAULT 'member'"),
            ("matches_in_club", "INTEGER DEFAULT 0"),
            ("wins_in_club", "INTEGER DEFAULT 0"),
            ("rating_in_club", "FLOAT DEFAULT 1000.0"),
        ]

        # Check if id column exists (might be composite PK)
        if not await column_exists("club_members", "id"):
            # Need to recreate table or add id column carefully
            print("⚠️  club_members.id missing - needs manual fix")

        for col, type_ in club_member_columns[1:]:  # Skip id for now
            if not await column_exists("club_members", col):
                print(f"➕ Adding club_members.{col}")
                await conn.execute(text(f"ALTER TABLE club_members ADD COLUMN {col} {type_}"))

        # ========== SESSIONS TABLE ==========
        session_columns = [
            ("location", "VARCHAR"),
            ("max_participants", "INTEGER DEFAULT 20"),
            ("created_by", "VARCHAR REFERENCES users(id)"),
            ("number_of_courts", "INTEGER DEFAULT 1"),
            ("court_cost_per_hour", "FLOAT"),
            ("total_court_cost", "FLOAT"),
            ("payment_type", "VARCHAR DEFAULT 'split'"),
            ("buffet_price", "FLOAT"),
            ("updated_at", "TIMESTAMP"),
        ]

        for col, type_ in session_columns:
            if not await column_exists("sessions", col):
                print(f"➕ Adding sessions.{col}")
                await conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {col} {type_}"))

        # ========== MATCHES TABLE ==========
        match_columns = [
            ("match_type", "VARCHAR DEFAULT 'single'"),
            ("team_a_player_2_id", "VARCHAR REFERENCES users(id)"),
            ("team_b_player_2_id", "VARCHAR REFERENCES users(id)"),
            ("winner_team", "VARCHAR"),
            ("set_scores", "JSONB"),
            ("score", "VARCHAR"),
            ("shuttlecocks_used", "INTEGER DEFAULT 0"),
            ("shuttlecock_price", "FLOAT"),
            ("started_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
        ]

        for col, type_ in match_columns:
            if not await column_exists("matches", col):
                print(f"➕ Adding matches.{col}")
                await conn.execute(text(f"ALTER TABLE matches ADD COLUMN {col} {type_}"))

        # ========== SESSION_REGISTRATIONS TABLE ==========
        reg_columns = [
            ("id", "SERIAL PRIMARY KEY"),
            ("waitlist_position", "INTEGER"),
            ("checked_in_at", "TIMESTAMP"),
            ("checked_out_at", "TIMESTAMP"),
        ]

        # Check if id exists
        if not await column_exists("session_registrations", "id"):
            print("⚠️  session_registrations.id missing - needs manual fix")

        for col, type_ in reg_columns[1:]:
            if not await column_exists("session_registrations", col):
                print(f"➕ Adding session_registrations.{col}")
                await conn.execute(text(f"ALTER TABLE session_registrations ADD COLUMN {col} {type_}"))

        print("✅ Migration complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
