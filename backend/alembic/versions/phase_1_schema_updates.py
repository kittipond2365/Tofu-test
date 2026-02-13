"""Add club owner, verification, moderators and super admin

Revision ID: phase_1_schema_updates
Revises: 
Create Date: 2025-02-13 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'phase_1_schema_updates'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=True, server_default='false'))
    
    # Add new columns to clubs table
    op.add_column('clubs', sa.Column('owner_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True))
    op.add_column('clubs', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('clubs', sa.Column('verified_by', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True))
    op.add_column('clubs', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('clubs', sa.Column('previous_owner_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True))
    op.add_column('clubs', sa.Column('transferred_at', sa.DateTime(), nullable=True))
    
    # Create foreign key constraints for clubs
    op.create_foreign_key('fk_clubs_owner_id', 'clubs', 'users', ['owner_id'], ['id'])
    op.create_foreign_key('fk_clubs_verified_by', 'clubs', 'users', ['verified_by'], ['id'])
    op.create_foreign_key('fk_clubs_previous_owner_id', 'clubs', 'users', ['previous_owner_id'], ['id'])
    
    # Create club_moderators table
    op.create_table(
        'club_moderators',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('club_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('appointed_by', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('appointed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('club_id', 'user_id', name='uq_club_moderator')
    )
    
    # Create foreign keys for club_moderators
    op.create_foreign_key('fk_club_moderators_club_id', 'club_moderators', 'clubs', ['club_id'], ['id'])
    op.create_foreign_key('fk_club_moderators_user_id', 'club_moderators', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_club_moderators_appointed_by', 'club_moderators', 'users', ['appointed_by'], ['id'])


def downgrade() -> None:
    # Drop club_moderators table
    op.drop_table('club_moderators')
    
    # Drop foreign keys from clubs
    op.drop_constraint('fk_clubs_owner_id', 'clubs', type_='foreignkey')
    op.drop_constraint('fk_clubs_verified_by', 'clubs', type_='foreignkey')
    op.drop_constraint('fk_clubs_previous_owner_id', 'clubs', type_='foreignkey')
    
    # Drop columns from clubs
    op.drop_column('clubs', 'transferred_at')
    op.drop_column('clubs', 'previous_owner_id')
    op.drop_column('clubs', 'verified_at')
    op.drop_column('clubs', 'verified_by')
    op.drop_column('clubs', 'is_verified')
    op.drop_column('clubs', 'owner_id')
    
    # Drop column from users
    op.drop_column('users', 'is_super_admin')