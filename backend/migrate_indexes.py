"""
Database migration script to add performance indexes.
Run this after deploying the new models.
"""
import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, '/app')

from app.core.database import sync_engine


# SQL statements to add indexes
INDEXES = [
    # Users table indexes
    ("ix_users_created_at", "CREATE INDEX IF NOT EXISTS ix_users_created_at ON users (created_at)"),
    ("ix_users_rating", "CREATE INDEX IF NOT EXISTS ix_users_rating ON users (rating DESC)"),
    
    # Clubs table indexes
    ("ix_clubs_is_public", "CREATE INDEX IF NOT EXISTS ix_clubs_is_public ON clubs (is_public)"),
    ("ix_clubs_created_at", "CREATE INDEX IF NOT EXISTS ix_clubs_created_at ON clubs (created_at)"),
    
    # Club members indexes
    ("ix_club_members_club_id", "CREATE INDEX IF NOT EXISTS ix_club_members_club_id ON club_members (club_id)"),
    ("ix_club_members_user_id", "CREATE INDEX IF NOT EXISTS ix_club_members_user_id ON club_members (user_id)"),
    ("ix_club_members_role", "CREATE INDEX IF NOT EXISTS ix_club_members_role ON club_members (role)"),
    ("ix_club_members_rating", "CREATE INDEX IF NOT EXISTS ix_club_members_rating ON club_members (rating_in_club DESC)"),
    
    # Sessions indexes
    ("ix_sessions_club_id", "CREATE INDEX IF NOT EXISTS ix_sessions_club_id ON sessions (club_id)"),
    ("ix_sessions_status", "CREATE INDEX IF NOT EXISTS ix_sessions_status ON sessions (status)"),
    ("ix_sessions_start_time", "CREATE INDEX IF NOT EXISTS ix_sessions_start_time ON sessions (start_time DESC)"),
    ("ix_sessions_created_by", "CREATE INDEX IF NOT EXISTS ix_sessions_created_by ON sessions (created_by)"),
    ("ix_sessions_club_status", "CREATE INDEX IF NOT EXISTS ix_sessions_club_status ON sessions (club_id, status)"),
    
    # Session registrations indexes
    ("ix_session_registrations_session_id", "CREATE INDEX IF NOT EXISTS ix_session_registrations_session_id ON session_registrations (session_id)"),
    ("ix_session_registrations_user_id", "CREATE INDEX IF NOT EXISTS ix_session_registrations_user_id ON session_registrations (user_id)"),
    ("ix_session_registrations_status", "CREATE INDEX IF NOT EXISTS ix_session_registrations_status ON session_registrations (status)"),
    ("ix_session_registrations_waitlist", "CREATE INDEX IF NOT EXISTS ix_session_registrations_waitlist ON session_registrations (session_id, waitlist_position)"),
    
    # Matches indexes
    ("ix_matches_session_id", "CREATE INDEX IF NOT EXISTS ix_matches_session_id ON matches (session_id)"),
    ("ix_matches_status", "CREATE INDEX IF NOT EXISTS ix_matches_status ON matches (status)"),
    ("ix_matches_completed_at", "CREATE INDEX IF NOT EXISTS ix_matches_completed_at ON matches (completed_at DESC)"),
    ("ix_matches_team_a_p1", "CREATE INDEX IF NOT EXISTS ix_matches_team_a_p1 ON matches (team_a_player_1_id)"),
    ("ix_matches_team_b_p1", "CREATE INDEX IF NOT EXISTS ix_matches_team_b_p1 ON matches (team_b_player_1_id)"),
    ("ix_matches_winner_team", "CREATE INDEX IF NOT EXISTS ix_matches_winner_team ON matches (winner_team)"),
]


def create_indexes():
    """Create all performance indexes"""
    print("Creating database indexes for performance optimization...")
    print("=" * 60)
    
    with sync_engine.connect() as conn:
        for index_name, sql in INDEXES:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️  Index {index_name}: {e}")
                conn.rollback()
    
    print("=" * 60)
    print("Index creation complete!")


def verify_indexes():
    """Verify indexes were created"""
    print("\nVerifying indexes...")
    print("=" * 60)
    
    with sync_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE 'ix_%'
            ORDER BY tablename, indexname
        """))
        
        indexes = result.fetchall()
        print(f"Found {len(indexes)} custom indexes:")
        for idx in indexes:
            print(f"  - {idx[0]} on {idx[1]}")
    
    print("=" * 60)


def analyze_tables():
    """Run ANALYZE on all tables for query optimizer"""
    print("\nRunning ANALYZE on all tables...")
    
    tables = ['users', 'clubs', 'club_members', 'sessions', 'session_registrations', 'matches']
    
    with sync_engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"ANALYZE {table}"))
                conn.commit()
                print(f"  ✅ Analyzed {table}")
            except Exception as e:
                print(f"  ⚠️  Failed to analyze {table}: {e}")
    
    print("Analysis complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration utilities')
    parser.add_argument('--create-indexes', action='store_true', help='Create performance indexes')
    parser.add_argument('--verify', action='store_true', help='Verify indexes exist')
    parser.add_argument('--analyze', action='store_true', help='Run ANALYZE on tables')
    parser.add_argument('--all', action='store_true', help='Run all operations')
    
    args = parser.parse_args()
    
    if args.all or args.create_indexes:
        create_indexes()
    
    if args.all or args.verify:
        verify_indexes()
    
    if args.all or args.analyze:
        analyze_tables()
    
    if not any([args.all, args.create_indexes, args.verify, args.analyze]):
        parser.print_help()
