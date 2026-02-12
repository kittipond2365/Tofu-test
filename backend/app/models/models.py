import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, 
    Text, Boolean, Float, Enum, UniqueConstraint
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


# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True, index=True)  # Optional for LINE users
    hashed_password = Column(String(255), nullable=True)  # Null for LINE users
    full_name = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    fcm_token = Column(String(255), nullable=True)  # Firebase Cloud Messaging token
    line_user_id = Column(String(100), unique=True, nullable=True)  # LINE Login user ID
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


class Club(Base):
    __tablename__ = "clubs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    
    # Settings
    max_members = Column(Integer, default=100)
    is_public = Column(Boolean, default=False)  # False = invite only
    
    # LINE Notify
    line_notify_token = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="club", cascade="all, delete-orphan")


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


class SessionRegistration(Base):
    __tablename__ = "session_registrations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.CONFIRMED)
    waitlist_position = Column(Integer, nullable=True)  # NULL if confirmed
    
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="registrations")
    user = relationship("User", back_populates="registrations")
    
    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_session_registration'),
    )


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    court_number = Column(Integer, default=1)
    
    # Team A
    team_a_player_1_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_a_player_2_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # NULL for singles
    
    # Team B
    team_b_player_1_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_b_player_2_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # NULL for singles
    
    # Scores (stored as JSON-like string for flexibility)
    # Format: "21-19,18-21,21-15" for best of 3
    score = Column(String(50), nullable=True)
    winner_team = Column(String(1), nullable=True)  # 'A' or 'B'
    
    status = Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="matches")
