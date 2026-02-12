"""
Enhanced database models with indexes and performance optimizations.
SQLModel version with full type safety.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, Enum, ForeignKey, UniqueConstraint, Index


def generate_uuid() -> str:
    return str(uuid.uuid4())


# Enums
class UserRole(str, PyEnum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    MEMBER = "member"


class SessionStatus(str, PyEnum):
    DRAFT = "draft"
    OPEN = "open"
    FULL = "full"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RegistrationStatus(str, PyEnum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class MatchStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_rating', 'rating'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    email: Optional[str] = Field(default=None, max_length=255, unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    full_name: str = Field(max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    fcm_token: Optional[str] = Field(default=None, max_length=255)
    line_user_id: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    # Player stats summary
    total_matches: int = Field(default=0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    rating: float = Field(default=1000.0)

    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    # Relationships
    club_memberships: List["ClubMember"] = Relationship(back_populates="user", cascade_delete=True)
    registrations: List["SessionRegistration"] = Relationship(back_populates="user", cascade_delete=True)


class Club(SQLModel, table=True):
    __tablename__ = "clubs"
    __table_args__ = (
        Index('ix_clubs_is_public', 'is_public'),
        Index('ix_clubs_created_at', 'created_at'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    location: Optional[str] = Field(default=None, max_length=500)

    max_members: int = Field(default=100)
    is_public: bool = Field(default=False)

    line_notify_token: Optional[str] = Field(default=None, max_length=255)

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    # Relationships
    members: List["ClubMember"] = Relationship(back_populates="club", cascade_delete=True)
    sessions: List["Session"] = Relationship(back_populates="club", cascade_delete=True)


class ClubMember(SQLModel, table=True):
    __tablename__ = "club_members"
    __table_args__ = (
        UniqueConstraint('club_id', 'user_id', name='uq_club_member'),
        Index('ix_club_members_club_id', 'club_id'),
        Index('ix_club_members_user_id', 'user_id'),
        Index('ix_club_members_role', 'role'),
        Index('ix_club_members_rating', 'rating_in_club'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    club_id: str = Field(foreign_key="clubs.id", max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    role: Optional[UserRole] = Field(default=UserRole.MEMBER, sa_column=Column(Enum(UserRole), default=UserRole.MEMBER))

    matches_in_club: int = Field(default=0)
    wins_in_club: int = Field(default=0)
    rating_in_club: float = Field(default=1000.0)

    joined_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    club: Optional[Club] = Relationship(back_populates="members")
    user: Optional[User] = Relationship(back_populates="club_memberships")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    __table_args__ = (
        Index('ix_sessions_club_id', 'club_id'),
        Index('ix_sessions_status', 'status'),
        Index('ix_sessions_start_time', 'start_time'),
        Index('ix_sessions_created_by', 'created_by'),
        Index('ix_sessions_club_status', 'club_id', 'status'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    club_id: str = Field(foreign_key="clubs.id", max_length=36)

    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    location: str = Field(max_length=500)

    start_time: datetime
    end_time: datetime

    max_participants: int = Field(default=20)
    status: Optional[SessionStatus] = Field(default=SessionStatus.DRAFT, sa_column=Column(Enum(SessionStatus), default=SessionStatus.DRAFT))

    created_by: str = Field(foreign_key="users.id", max_length=36)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    # Relationships
    club: Optional[Club] = Relationship(back_populates="sessions")
    registrations: List["SessionRegistration"] = Relationship(back_populates="session", cascade_delete=True)
    matches: List["Match"] = Relationship(back_populates="session", cascade_delete=True)


class SessionRegistration(SQLModel, table=True):
    __tablename__ = "session_registrations"
    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_session_registration'),
        Index('ix_session_registrations_session_id', 'session_id'),
        Index('ix_session_registrations_user_id', 'user_id'),
        Index('ix_session_registrations_status', 'status'),
        Index('ix_session_registrations_waitlist', 'session_id', 'waitlist_position'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    session_id: str = Field(foreign_key="sessions.id", max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)

    status: Optional[RegistrationStatus] = Field(default=RegistrationStatus.CONFIRMED, sa_column=Column(Enum(RegistrationStatus), default=RegistrationStatus.CONFIRMED))
    waitlist_position: Optional[int] = Field(default=None)

    checked_in_at: Optional[datetime] = Field(default=None)
    checked_out_at: Optional[datetime] = Field(default=None)

    registered_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    session: Optional[Session] = Relationship(back_populates="registrations")
    user: Optional[User] = Relationship(back_populates="registrations")


class Match(SQLModel, table=True):
    __tablename__ = "matches"
    __table_args__ = (
        Index('ix_matches_session_id', 'session_id'),
        Index('ix_matches_status', 'status'),
        Index('ix_matches_completed_at', 'completed_at'),
        Index('ix_matches_team_a_p1', 'team_a_player_1_id'),
        Index('ix_matches_team_b_p1', 'team_b_player_1_id'),
        Index('ix_matches_winner_team', 'winner_team'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    session_id: str = Field(foreign_key="sessions.id", max_length=36)

    court_number: int = Field(default=1)

    team_a_player_1_id: str = Field(foreign_key="users.id", max_length=36)
    team_a_player_2_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)

    team_b_player_1_id: str = Field(foreign_key="users.id", max_length=36)
    team_b_player_2_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)

    score: Optional[str] = Field(default=None, max_length=50)
    winner_team: Optional[str] = Field(default=None, max_length=1)

    status: Optional[MatchStatus] = Field(default=MatchStatus.SCHEDULED, sa_column=Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED))

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    session: Optional[Session] = Relationship(back_populates="matches")
