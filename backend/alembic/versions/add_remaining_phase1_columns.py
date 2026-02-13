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
    # Add missing columns to users table
    op.add_column('users', sa.Column('picture_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # ========== CLUBS TABLE ==========
    # Add missing columns to clubs table
    op.add_column('clubs', sa.Column('payment_qr_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('clubs', sa.Column('payment_method_note', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('clubs', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # ========== CLUB_MEMBERS TABLE ==========
    # Add role column to club_members
    op.add_column('club_members', sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='member'))
    
    # ========== SESSIONS TABLE ==========
    # Add missing columns to sessions table
    op.add_column('sessions', sa.Column('number_of_courts', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('sessions', sa.Column('court_cost_per_hour', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('total_court_cost', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('payment_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='split'))
    op.add_column('sessions', sa.Column('buffet_price', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # ========== MATCHES TABLE ==========
    # Add missing columns to matches table
    op.add_column('matches', sa.Column('match_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='single'))
    op.add_column('matches', sa.Column('team_a_player_2_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True))
    op.add_column('matches', sa.Column('team_b_player_2_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True))
    op.add_column('matches', sa.Column('winner_team', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('matches', sa.Column('set_scores', sa.JSON(), nullable=True))
    op.add_column('matches', sa.Column('shuttlecocks_used', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('matches', sa.Column('shuttlecock_price', sa.Float(), nullable=True))
    op.add_column('matches', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('matches', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Create foreign keys for matches player columns
    op.create_foreign_key('fk_matches_team_a_player_2', 'matches', 'users', ['team_a_player_2_id'], ['id'])
    op.create_foreign_key('fk_matches_team_b_player_2', 'matches', 'users', ['team_b_player_2_id'], ['id'])
    
    # ========== NEW TABLES ==========
    
    # Create inbox_messages table
    op.create_table(
        'inbox_messages',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('message', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('message_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='notification'),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('qr_code_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True),
        sa.Column('proof_image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('proof_uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('proof_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create foreign keys for inbox_messages
    op.create_foreign_key('fk_inbox_messages_user_id', 'inbox_messages', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_inbox_messages_session_id', 'inbox_messages', 'sessions', ['session_id'], ['id'])
    
    # Create courts table
    op.create_table(
        'courts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('court_number', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='available'),
        sa.Column('auto_matching_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('current_match_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create foreign keys for courts
    op.create_foreign_key('fk_courts_session_id', 'courts', 'sessions', ['session_id'], ['id'])
    op.create_foreign_key('fk_courts_current_match_id', 'courts', 'matches', ['current_match_id'], ['id'])
    
    # Create pre_matches table
    op.create_table(
        'pre_matches',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('match_order', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('team_a_player_1_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('team_a_player_2_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True),
        sa.Column('team_b_player_1_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
        sa.Column('team_b_player_2_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=True, server_default='queued'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create foreign keys for pre_matches
    op.create_foreign_key('fk_pre_matches_session_id', 'pre_matches', 'sessions', ['session_id'], ['id'])
    op.create_foreign_key('fk_pre_matches_team_a_player_1', 'pre_matches', 'users', ['team_a_player_1_id'], ['id'])
    op.create_foreign_key('fk_pre_matches_team_a_player_2', 'pre_matches', 'users', ['team_a_player_2_id'], ['id'])
    op.create_foreign_key('fk_pre_matches_team_b_player_1', 'pre_matches', 'users', ['team_b_player_1_id'], ['id'])
    op.create_foreign_key('fk_pre_matches_team_b_player_2', 'pre_matches', 'users', ['team_b_player_2_id'], ['id'])


def downgrade() -> None:
    # Drop pre_matches table
    op.drop_constraint('fk_pre_matches_session_id', 'pre_matches', type_='foreignkey')
    op.drop_constraint('fk_pre_matches_team_a_player_1', 'pre_matches', type_='foreignkey')
    op.drop_constraint('fk_pre_matches_team_a_player_2', 'pre_matches', type_='foreignkey')
    op.drop_constraint('fk_pre_matches_team_b_player_1', 'pre_matches', type_='foreignkey')
    op.drop_constraint('fk_pre_matches_team_b_player_2', 'pre_matches', type_='foreignkey')
    op.drop_table('pre_matches')
    
    # Drop courts table
    op.drop_constraint('fk_courts_session_id', 'courts', type_='foreignkey')
    op.drop_constraint('fk_courts_current_match_id', 'courts', type_='foreignkey')
    op.drop_table('courts')
    
    # Drop inbox_messages table
    op.drop_constraint('fk_inbox_messages_user_id', 'inbox_messages', type_='foreignkey')
    op.drop_constraint('fk_inbox_messages_session_id', 'inbox_messages', type_='foreignkey')
    op.drop_table('inbox_messages')
    
    # Drop foreign keys from matches
    op.drop_constraint('fk_matches_team_a_player_2', 'matches', type_='foreignkey')
    op.drop_constraint('fk_matches_team_b_player_2', 'matches', type_='foreignkey')
    
    # Drop columns from matches
    op.drop_column('matches', 'completed_at')
    op.drop_column('matches', 'started_at')
    op.drop_column('matches', 'shuttlecock_price')
    op.drop_column('matches', 'shuttlecocks_used')
    op.drop_column('matches', 'set_scores')
    op.drop_column('matches', 'winner_team')
    op.drop_column('matches', 'team_b_player_2_id')
    op.drop_column('matches', 'team_a_player_2_id')
    op.drop_column('matches', 'match_type')
    
    # Drop columns from sessions
    op.drop_column('sessions', 'updated_at')
    op.drop_column('sessions', 'buffet_price')
    op.drop_column('sessions', 'payment_type')
    op.drop_column('sessions', 'total_court_cost')
    op.drop_column('sessions', 'court_cost_per_hour')
    op.drop_column('sessions', 'number_of_courts')
    
    # Drop column from club_members
    op.drop_column('club_members', 'role')
    
    # Drop columns from clubs
    op.drop_column('clubs', 'updated_at')
    op.drop_column('clubs', 'payment_method_note')
    op.drop_column('clubs', 'payment_qr_url')
    
    # Drop columns from users
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'email')
    op.drop_column('users', 'picture_url')
