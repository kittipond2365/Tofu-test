"""Add missing club columns emergency

Revision ID: add_missing_club_columns_emergency
Revises: add_all_missing_fields_from_audit
Create Date: 2026-02-14 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "add_missing_club_columns_emergency"
down_revision: Union[str, None] = "add_all_missing_fields_from_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='invite_code') THEN
                ALTER TABLE clubs ADD COLUMN invite_code VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='invite_qr_url') THEN
                ALTER TABLE clubs ADD COLUMN invite_qr_url VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='payment_qr_url') THEN
                ALTER TABLE clubs ADD COLUMN payment_qr_url VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='payment_method_note') THEN
                ALTER TABLE clubs ADD COLUMN payment_method_note VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clubs' AND column_name='updated_at') THEN
                ALTER TABLE clubs ADD COLUMN updated_at TIMESTAMP;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    pass
