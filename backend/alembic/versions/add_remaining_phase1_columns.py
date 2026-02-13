"""Add remaining Phase 1 columns and tables

Revision ID: add_remaining_phase1_columns
Revises: phase_1_schema_updates
Create Date: 2026-02-14 00:08:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'add_remaining_phase1_columns'
down_revision: Union[str, None] = 'phase_1_schema_updates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== USERS TABLE ==========
    # Add missing columns to users table (with IF NOT EXISTS)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='users' AND column_name='picture_url') THEN
                ALTER TABLE users ADD COLUMN picture_url VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='users' AND column_name='email') THEN
                ALTER TABLE users ADD COLUMN email VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='users' AND column_name='phone') THEN
                ALTER TABLE users ADD COLUMN phone VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='users' AND column_name='updated_at') THEN
                ALTER TABLE users ADD COLUMN updated_at TIMESTAMP;
            END IF;
        END $$;
    """)
    
    # ========== CLUBS TABLE ==========
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='clubs' AND column_name='payment_qr_url') THEN
                ALTER TABLE clubs ADD COLUMN payment_qr_url VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='clubs' AND column_name='payment_method_note') THEN
                ALTER TABLE clubs ADD COLUMN payment_method_note VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='clubs' AND column_name='updated_at') THEN
                ALTER TABLE clubs ADD COLUMN updated_at TIMESTAMP;
            END IF;
        END $$;
    """)
    
    # ========== CLUB_MEMBERS TABLE ==========
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='club_members' AND column_name='role') THEN
                ALTER TABLE club_members ADD COLUMN role VARCHAR DEFAULT 'member';
            END IF;
        END $$;
    """)
    
    # ========== SESSIONS TABLE ==========
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='number_of_courts') THEN
                ALTER TABLE sessions ADD COLUMN number_of_courts INTEGER DEFAULT 1;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='court_cost_per_hour') THEN
                ALTER TABLE sessions ADD COLUMN court_cost_per_hour FLOAT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='total_court_cost') THEN
                ALTER TABLE sessions ADD COLUMN total_court_cost FLOAT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='payment_type') THEN
                ALTER TABLE sessions ADD COLUMN payment_type VARCHAR DEFAULT 'split';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='buffet_price') THEN
                ALTER TABLE sessions ADD COLUMN buffet_price FLOAT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='sessions' AND column_name='updated_at') THEN
                ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP;
            END IF;
        END $$;
    """)
    
    # ========== MATCHES TABLE ==========
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='match_type') THEN
                ALTER TABLE matches ADD COLUMN match_type VARCHAR DEFAULT 'single';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='team_a_player_2_id') THEN
                ALTER TABLE matches ADD COLUMN team_a_player_2_id VARCHAR(36);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='team_b_player_2_id') THEN
                ALTER TABLE matches ADD COLUMN team_b_player_2_id VARCHAR(36);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='winner_team') THEN
                ALTER TABLE matches ADD COLUMN winner_team VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='set_scores') THEN
                ALTER TABLE matches ADD COLUMN set_scores JSON;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='shuttlecocks_used') THEN
                ALTER TABLE matches ADD COLUMN shuttlecocks_used INTEGER DEFAULT 0;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='shuttlecock_price') THEN
                ALTER TABLE matches ADD COLUMN shuttlecock_price FLOAT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='started_at') THEN
                ALTER TABLE matches ADD COLUMN started_at TIMESTAMP;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='matches' AND column_name='completed_at') THEN
                ALTER TABLE matches ADD COLUMN completed_at TIMESTAMP;
            END IF;
        END $$;
    """)
    
    # Create foreign keys for matches player columns (with IF NOT EXISTS)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name='fk_matches_team_a_player_2') THEN
                ALTER TABLE matches ADD CONSTRAINT fk_matches_team_a_player_2 
                    FOREIGN KEY (team_a_player_2_id) REFERENCES users(id);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name='fk_matches_team_b_player_2') THEN
                ALTER TABLE matches ADD CONSTRAINT fk_matches_team_b_player_2 
                    FOREIGN KEY (team_b_player_2_id) REFERENCES users(id);
            END IF;
        END $$;
    """)
    
    # ========== NEW TABLES ==========
    # Create inbox_messages table with IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS inbox_messages (
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
    """)
    
    # Create courts table with IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS courts (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
            court_number INTEGER NOT NULL,
            status VARCHAR DEFAULT 'available',
            auto_matching_enabled BOOLEAN DEFAULT TRUE,
            current_match_id VARCHAR(36) REFERENCES matches(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    """)
    
    # Create pre_matches table with IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS pre_matches (
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
    """)
    
    # Create club_moderators table with IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS club_moderators (
            id VARCHAR(36) PRIMARY KEY,
            club_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            appointed_by VARCHAR(36) NOT NULL,
            appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE (club_id, user_id)
        )
    """)


def downgrade() -> None:
    # Drop club_moderators table
    op.execute("DROP TABLE IF EXISTS club_moderators CASCADE")
    
    # Drop pre_matches table
    op.execute("DROP TABLE IF EXISTS pre_matches CASCADE")
    
    # Drop courts table
    op.execute("DROP TABLE IF EXISTS courts CASCADE")
    
    # Drop inbox_messages table
    op.execute("DROP TABLE IF EXISTS inbox_messages CASCADE")
    
    # Drop foreign keys from matches
    op.execute("ALTER TABLE matches DROP CONSTRAINT IF EXISTS fk_matches_team_a_player_2")
    op.execute("ALTER TABLE matches DROP CONSTRAINT IF EXISTS fk_matches_team_b_player_2")
    
    # Drop columns from matches
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS completed_at")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS started_at")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS shuttlecock_price")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS shuttlecocks_used")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS set_scores")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS winner_team")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS team_b_player_2_id")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS team_a_player_2_id")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS match_type")
    
    # Drop columns from sessions
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS buffet_price")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS payment_type")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS total_court_cost")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS court_cost_per_hour")
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS number_of_courts")
    
    # Drop column from club_members
    op.execute("ALTER TABLE club_members DROP COLUMN IF EXISTS role")
    
    # Drop columns from clubs
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS payment_method_note")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS payment_qr_url")
    
    # Drop columns from users
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS picture_url")
