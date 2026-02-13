"""Add all missing fields from audit

Revision ID: add_all_missing_fields_from_audit
Revises: add_remaining_phase1_columns
Create Date: 2026-02-14 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "add_all_missing_fields_from_audit"
down_revision: Union[str, None] = "add_remaining_phase1_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='full_name') THEN
                ALTER TABLE users ADD COLUMN full_name VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='hashed_password') THEN
                ALTER TABLE users ADD COLUMN hashed_password VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_active') THEN
                ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_verified') THEN
                ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='rating') THEN
                ALTER TABLE users ADD COLUMN rating DOUBLE PRECISION NOT NULL DEFAULT 1000.0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='total_matches') THEN
                ALTER TABLE users ADD COLUMN total_matches INTEGER NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='wins') THEN
                ALTER TABLE users ADD COLUMN wins INTEGER NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='losses') THEN
                ALTER TABLE users ADD COLUMN losses INTEGER NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='fcm_token') THEN
                ALTER TABLE users ADD COLUMN fcm_token VARCHAR;
            END IF;
        END $$;
    """)

    # sessions
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sessions' AND column_name='location') THEN
                ALTER TABLE sessions ADD COLUMN location VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sessions' AND column_name='max_participants') THEN
                ALTER TABLE sessions ADD COLUMN max_participants INTEGER NOT NULL DEFAULT 20;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sessions' AND column_name='created_by') THEN
                ALTER TABLE sessions ADD COLUMN created_by VARCHAR;
            END IF;
        END $$;
    """)

    # session_registrations
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='session_registrations' AND column_name='id') THEN
                ALTER TABLE session_registrations ADD COLUMN id SERIAL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='session_registrations' AND column_name='waitlist_position') THEN
                ALTER TABLE session_registrations ADD COLUMN waitlist_position INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='session_registrations' AND column_name='checked_in_at') THEN
                ALTER TABLE session_registrations ADD COLUMN checked_in_at TIMESTAMP;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='session_registrations' AND column_name='checked_out_at') THEN
                ALTER TABLE session_registrations ADD COLUMN checked_out_at TIMESTAMP;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_session_user') THEN
                ALTER TABLE session_registrations ADD CONSTRAINT uq_session_user UNIQUE (session_id, user_id);
            END IF;
        END $$;
    """)

    # club_members
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='club_members' AND column_name='id') THEN
                ALTER TABLE club_members ADD COLUMN id SERIAL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='club_members' AND column_name='matches_in_club') THEN
                ALTER TABLE club_members ADD COLUMN matches_in_club INTEGER NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='club_members' AND column_name='wins_in_club') THEN
                ALTER TABLE club_members ADD COLUMN wins_in_club INTEGER NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='club_members' AND column_name='rating_in_club') THEN
                ALTER TABLE club_members ADD COLUMN rating_in_club DOUBLE PRECISION NOT NULL DEFAULT 1000.0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_club_member') THEN
                ALTER TABLE club_members ADD CONSTRAINT uq_club_member UNIQUE (club_id, user_id);
            END IF;
        END $$;
    """)

    # matches
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='matches' AND column_name='score') THEN
                ALTER TABLE matches ADD COLUMN score VARCHAR;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Intentionally conservative: avoid destructive schema drops in downgrade.
    pass
