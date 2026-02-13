"""Add club owner, verification, moderators and super admin

Revision ID: phase_1_schema_updates
Revises:
Create Date: 2025-02-13 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'phase_1_schema_updates'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_super_admin') THEN
                ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='owner_id') THEN
                ALTER TABLE clubs ADD COLUMN owner_id VARCHAR(36);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='is_verified') THEN
                ALTER TABLE clubs ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='verified_by') THEN
                ALTER TABLE clubs ADD COLUMN verified_by VARCHAR(36);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='verified_at') THEN
                ALTER TABLE clubs ADD COLUMN verified_at TIMESTAMP;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='previous_owner_id') THEN
                ALTER TABLE clubs ADD COLUMN previous_owner_id VARCHAR(36);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='transferred_at') THEN
                ALTER TABLE clubs ADD COLUMN transferred_at TIMESTAMP;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='clubs' AND constraint_name='fk_clubs_owner_id') THEN
                ALTER TABLE clubs ADD CONSTRAINT fk_clubs_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='clubs' AND constraint_name='fk_clubs_verified_by') THEN
                ALTER TABLE clubs ADD CONSTRAINT fk_clubs_verified_by FOREIGN KEY (verified_by) REFERENCES users(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='clubs' AND constraint_name='fk_clubs_previous_owner_id') THEN
                ALTER TABLE clubs ADD CONSTRAINT fk_clubs_previous_owner_id FOREIGN KEY (previous_owner_id) REFERENCES users(id);
            END IF;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS club_moderators (
            id VARCHAR(36) PRIMARY KEY,
            club_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            appointed_by VARCHAR(36) NOT NULL,
            appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_club_moderator UNIQUE (club_id, user_id)
        )
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='club_moderators' AND constraint_name='fk_club_moderators_club_id') THEN
                ALTER TABLE club_moderators ADD CONSTRAINT fk_club_moderators_club_id FOREIGN KEY (club_id) REFERENCES clubs(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='club_moderators' AND constraint_name='fk_club_moderators_user_id') THEN
                ALTER TABLE club_moderators ADD CONSTRAINT fk_club_moderators_user_id FOREIGN KEY (user_id) REFERENCES users(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='club_moderators' AND constraint_name='fk_club_moderators_appointed_by') THEN
                ALTER TABLE club_moderators ADD CONSTRAINT fk_club_moderators_appointed_by FOREIGN KEY (appointed_by) REFERENCES users(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS club_moderators CASCADE")
    op.execute("ALTER TABLE clubs DROP CONSTRAINT IF EXISTS fk_clubs_owner_id")
    op.execute("ALTER TABLE clubs DROP CONSTRAINT IF EXISTS fk_clubs_verified_by")
    op.execute("ALTER TABLE clubs DROP CONSTRAINT IF EXISTS fk_clubs_previous_owner_id")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS transferred_at")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS previous_owner_id")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS verified_at")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS verified_by")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS is_verified")
    op.execute("ALTER TABLE clubs DROP COLUMN IF EXISTS owner_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_super_admin")
