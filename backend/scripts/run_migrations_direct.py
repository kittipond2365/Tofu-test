"""Direct database migration using SQLModel - SYNC VERSION"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get and normalize DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/badminton_db")

# Ensure sync URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

def migrate():
    print(f"🔄 Connecting to database...")
    engine = create_engine(DATABASE_URL, echo=False)
    
    with engine.begin() as conn:
        # Helper function to check if column exists
        def column_exists(table, column):
            result = conn.execute(text(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='{table}' AND column_name='{column}'
            """))
            return result.scalar() is not None
        
        # Helper function to check if table exists
        def table_exists(table):
            result = conn.execute(text(f"""
                SELECT 1 FROM information_schema.tables 
                WHERE table_name='{table}'
            """))
            return result.scalar() is not None
        
        # Add columns to users table
        columns_to_add = [
            ("users", "picture_url", "VARCHAR"),
            ("users", "email", "VARCHAR"),
            ("users", "phone", "VARCHAR"),
            ("users", "is_super_admin", "BOOLEAN DEFAULT FALSE"),
            ("users", "updated_at", "TIMESTAMP"),
        ]
        
        for table, column, col_type in columns_to_add:
            if not column_exists(table, column):
                print(f"➕ Adding {column} to {table}...")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            else:
                print(f"✅ {column} already exists in {table}")
        
        # Add columns to clubs table
        club_columns = [
            ("clubs", "payment_qr_url", "VARCHAR"),
            ("clubs", "payment_method_note", "VARCHAR"),
            ("clubs", "updated_at", "TIMESTAMP"),
        ]
        
        for table, column, col_type in club_columns:
            if not column_exists(table, column):
                print(f"➕ Adding {column} to {table}...")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            else:
                print(f"✅ {column} already exists in {table}")
        
        # Create new tables
        if not table_exists("club_moderators"):
            print("➕ Creating club_moderators table...")
            conn.execute(text("""
                CREATE TABLE club_moderators (
                    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
                    club_id VARCHAR(36) NOT NULL REFERENCES clubs(id),
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    appointed_by VARCHAR(36) NOT NULL REFERENCES users(id),
                    appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (club_id, user_id)
                )
            """))
        else:
            print("✅ club_moderators table already exists")
        
        if not table_exists("inbox_messages"):
            print("➕ Creating inbox_messages table...")
            conn.execute(text("""
                CREATE TABLE inbox_messages (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    title VARCHAR NOT NULL,
                    message VARCHAR NOT NULL,
                    message_type VARCHAR DEFAULT 'notification',
                    amount FLOAT,
                    qr_code_url VARCHAR,
                    session_id VARCHAR(36) REFERENCES sessions(id),
                    proof_image_url VARCHAR,
                    proof_uploaded_at TIMESTAMP,
                    proof_expires_at TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        else:
            print("✅ inbox_messages table already exists")
        
        if not table_exists("courts"):
            print("➕ Creating courts table...")
            conn.execute(text("""
                CREATE TABLE courts (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
                    court_number INTEGER NOT NULL,
                    status VARCHAR DEFAULT 'available',
                    auto_matching_enabled BOOLEAN DEFAULT TRUE,
                    current_match_id VARCHAR(36) REFERENCES matches(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """))
        else:
            print("✅ courts table already exists")
        
        if not table_exists("pre_matches"):
            print("➕ Creating pre_matches table...")
            conn.execute(text("""
                CREATE TABLE pre_matches (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
                    match_order INTEGER DEFAULT 1,
                    team_a_player_1_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    team_a_player_2_id VARCHAR(36) REFERENCES users(id),
                    team_b_player_1_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    team_b_player_2_id VARCHAR(36) REFERENCES users(id),
                    status VARCHAR DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activated_at TIMESTAMP
                )
            """))
        else:
            print("✅ pre_matches table already exists")
        
        print("✅ Migration complete!")
    
    engine.dispose()

if __name__ == "__main__":
    migrate()
