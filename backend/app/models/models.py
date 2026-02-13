import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, Enum, ForeignKey, UniqueConstraint


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


# Link models (must be defined before models that use them in link_model)
class ClubModerator(SQLModel, table=True):
    __tablename__ = "club_moderators"
    __table_args__ = (
        UniqueConstraint('club_id', 'user_id', name='uq_club_moderator'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    club_id: str = Field(foreign_key="clubs.id", max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    appointed_by: str = Field(foreign_key="users.id", max_length=36)
    appointed_at: datetime = Field(default_factory=datetime.utcnow)

    # Simple relationships WITHOUT back_populates (link_model handles the association)
    club: Optional["Club"] = Relationship()
    user: Optional["User"] = Relationship()
    appointed_by_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ClubModerator.appointed_by]"}
    )


class ClubMember(SQLModel, table=True):
    __tablename__ = "club_members"
    __table_args__ = (
        UniqueConstraint('club_id', 'user_id', name='uq_club_member'),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    club_id: str = Field(foreign_key="clubs.id", max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    role: Optional[UserRole] = Field(default=UserRole.MEMBER, sa_column=Column(Enum(UserRole), default=UserRole.MEMBER))

    # Club-specific stats
    matches_in_club: int = Field(default=0)
    wins_in_club: int = Field(default=0)
    rating_in_club: float = Field(default=1000.0)

    joined_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    club: Optional["Club"] = Relationship(back_populates="members")
    user: Optional["User"] = Relationship(back_populates="club_memberships")


class SessionRegistration(SQLModel, table=True):
    __tablename__ = "session_registrations"
    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_session_registration'),
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
    session: Optional["Session"] = Relationship(back_populates="registrations")
    user: Optional["User"] = Relationship(back_populates="registrations")


# Main models
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    email: Optional[str] = Field(default=None, max_length=255, unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    full_name: str = Field(max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    fcm_token: Optional[str] = Field(default=None, max_length=255)
    line_user_id: Optional[str] = Field(default=None, max_length=100, unique=True)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    # Player stats summary
    total_matches: int = Field(default=0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    rating: float = Field(default=1000.0)

    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    
    # NEW FIELDS for Phase 1
    is_super_admin: bool = Field(default=False)
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    # Relationships
    club_memberships: List["ClubMember"] = Relationship(back_populates="user", cascade_delete=True)
    registrations: List["SessionRegistration"] = Relationship(back_populates="user", cascade_delete=True)
    owned_clubs: List["Club"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )
    moderated_clubs: List["Club"] = Relationship(
        link_model=ClubModerator
    )


class Club(SQLModel, table=True):
    __tablename__ = "clubs"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    location: Optional[str] = Field(default=None, max_length=500)

    # Settings
    max_members: int = Field(default=100)
    is_public: bool = Field(default=False)

    # LINE Notify
    line_notify_token: Optional[str] = Field(default=None, max_length=255)
    
    # NEW FIELDS for Phase 1
    owner_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)
    is_verified: bool = Field(default=False)
    verified_by: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)
    verified_at: Optional[datetime] = Field(default=None)
    
    # For ownership transfer
    previous_owner_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)
    transferred_at: Optional[datetime] = Field(default=None)

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    # Relationships
    owner: Optional["User"] = Relationship(
        back_populates="owned_clubs",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )
    members: List["ClubMember"] = Relationship(back_populates="club", cascade_delete=True)
    sessions: List["Session"] = Relationship(back_populates="club", cascade_delete=True)
    moderators: List["User"] = Relationship(
        link_model=ClubModerator
    )


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

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


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=36)
    session_id: str = Field(foreign_key="sessions.id", max_length=36)

    court_number: int = Field(default=1)

    # Team A
    team_a_player_1_id: str = Field(foreign_key="users.id", max_length=36)
    team_a_player_2_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)

    # Team B
    team_b_player_1_id: str = Field(foreign_key="users.id", max_length=36)
    team_b_player_2_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=36)

    # Scores
    score: Optional[str] = Field(default=None, max_length=50)
    winner_team: Optional[str] = Field(default=None, max_length=1)

    status: Optional[MatchStatus] = Field(default=MatchStatus.SCHEDULED, sa_column=Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED))

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))

    # Relationships
    session: Optional[Session] = Relationship(back_populates="matches")
