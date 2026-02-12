"""
Enhanced database models with indexes and performance optimizations.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, 
    Text, Boolean, Float, Enum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    line_user_id = Column(String(100), unique=True, nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Player stats summary
    total_matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    rating = Column(Float, default=1000.0)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    club_memberships = relationship("ClubMember", back_populates="user", cascade="all, delete-orphan")
    registrations = relationship("SessionRegistration", back_populates="user", cascade="all, delete-orphan")
    
    # Additional indexes
    __table_args__ = (
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_rating', 'rating'),
    )


class Club(Base):
    __tablename__ = "clubs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    
    # Settings
    max_members = Column(Integer, default=100)
    is_public = Column(Boolean, default=False)
    
    # LINE Notify
    line_notify_token = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="club", cascade="all, delete-orphan")
    
    # Additional indexes
    __table_args__ = (
        Index('ix_clubs_is_public', 'is_public'),
        Index('ix_clubs_created_at', 'created_at'),
    )


class ClubMember(Base):
    __tablename__ = "club_members"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    club_id = Column(String(36), ForeignKey("clubs.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    
    # Club-specific stats
    matches_in_club = Column(Integer, default=0)
    wins_in_club = Column(Integer, default=0)
    rating_in_club = Column(Float, default=1000.0)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="members")
    user = relationship("User", back_populates="club_memberships")
    
    __table_args__ = (
        UniqueConstraint('club_id', 'user_id', name='uq_club_member'),
        # Performance indexes
        Index('ix_club_members_club_id', 'club_id'),
        Index('ix_club_members_user_id', 'user_id'),
        Index('ix_club_members_role', 'role'),
        Index('ix_club_members_rating', 'rating_in_club'),
    )


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    club_id = Column(String(36), ForeignKey("clubs.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=False)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    max_participants = Column(Integer, default=20)
    status = Column(Enum(SessionStatus), default=SessionStatus.DRAFT)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="sessions")
    registrations = relationship("SessionRegistration", back_populates="session", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Performance indexes
        Index('ix_sessions_club_id', 'club_id'),
        Index('ix_sessions_status', 'status'),
        Index('ix_sessions_start_time', 'start_time'),
        Index('ix_sessions_created_by', 'created_by'),
        # Composite index for common query pattern
        Index('ix_sessions_club_status', 'club_id', 'status'),
    )


class SessionRegistration(Base):
    __tablename__ = "session_registrations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.CONFIRMED)
    waitlist_position = Column(Integer, nullable=True)
    
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="registrations")
    user = relationship("User", back_populates="registrations")
    
    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_session_registration'),
        # Performance indexes
        Index('ix_session_registrations_session_id', 'session_id'),
        Index('ix_session_registrations_user_id', 'user_id'),
        Index('ix_session_registrations_status', 'status'),
        Index('ix_session_registrations_waitlist', 'session_id', 'waitlist_position'),
    )


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    court_number = Column(Integer, default=1)
    
    # Team A
    team_a_player_1_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_a_player_2_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Team B
    team_b_player_1_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_b_player_2_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Scores
    score = Column(String(50), nullable=True)
    winner_team = Column(String(1), nullable=True)
    
    status = Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="matches")
    
    __table_args__ = (
        # Performance indexes
        Index('ix_matches_session_id', 'session_id'),
        Index('ix_matches_status', 'status'),
        Index('ix_matches_completed_at', 'completed_at'),
        # Player lookup indexes
        Index('ix_matches_team_a_p1', 'team_a_player_1_id'),
        Index('ix_matches_team_b_p1', 'team_b_player_1_id'),
        Index('ix_matches_winner_team', 'winner_team'),
    )
