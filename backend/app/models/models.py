from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Column, JSON

from app.core.utils import utc_now


def now_utc() -> datetime:
    return utc_now()


# ============= ENUMS =============

class UserRole(str, Enum):
    OWNER = "owner"
    MODERATOR = "moderator"
    ORGANIZER = "organizer"
    MEMBER = "member"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    OPEN = "open"
    FULL = "full"
    ACTIVE = "active"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RegistrationStatus(str, Enum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    ATTENDED = "attended"


class PaymentType(str, Enum):
    SPLIT = "split"
    PER_SHUTTLE = "per_shuttle"
    BUFFET = "buffet"


class ClubPrivacy(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class MessageType(str, Enum):
    PAYMENT = "payment"
    NOTIFICATION = "notification"
    INVITE = "invite"
    RESULT = "result"


# ============= LINK TABLES (No relationships, just FKs) =============

class ClubMember(SQLModel, table=True):
    __tablename__ = "club_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    user_id: str = Field(foreign_key="users.id")
    role: str = Field(default="member")
    matches_in_club: int = Field(default=0)
    wins_in_club: int = Field(default=0)
    rating_in_club: float = Field(default=1000.0)
    joined_at: datetime = Field(default_factory=now_utc)

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_member"),
    )


class ClubModerator(SQLModel, table=True):
    __tablename__ = "club_moderators"

    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    user_id: str = Field(foreign_key="users.id")
    appointed_by: str = Field(foreign_key="users.id")
    appointed_at: datetime = Field(default_factory=now_utc)


class SessionRegistration(SQLModel, table=True):
    __tablename__ = "session_registrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    user_id: str = Field(foreign_key="users.id")
    waitlist_position: Optional[int] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    status: str = Field(default="confirmed")
    registered_at: datetime = Field(default_factory=now_utc)

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_session_user"),
    )


# ============= MAIN MODELS =============

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    line_user_id: str = Field(unique=True, index=True)
    display_name: str
    picture_url: Optional[str] = None

    full_name: Optional[str] = None
    hashed_password: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    rating: float = Field(default=1000.0)
    total_matches: int = Field(default=0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)

    fcm_token: Optional[str] = None
    is_super_admin: bool = Field(default=False)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    owned_clubs: List["Club"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )

    @property
    def avatar_url(self) -> Optional[str]:
        return self.picture_url

    @avatar_url.setter
    def avatar_url(self, value: Optional[str]):
        self.picture_url = value


class Club(SQLModel, table=True):
    __tablename__ = "clubs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
    location: Optional[str] = None
    max_members: int = Field(default=100)
    is_public: bool = Field(default=True)
    invite_code: Optional[str] = None
    invite_qr_url: Optional[str] = None

    owner_id: str = Field(foreign_key="users.id")

    is_verified: bool = Field(default=False)
    verified_by: Optional[str] = Field(foreign_key="users.id", default=None)
    verified_at: Optional[datetime] = None

    previous_owner_id: Optional[str] = Field(foreign_key="users.id", default=None)
    transferred_at: Optional[datetime] = None

    payment_qr_url: Optional[str] = None
    payment_method_note: Optional[str] = None

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    owner: Optional["User"] = Relationship(
        back_populates="owned_clubs",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )
    sessions: List["Session"] = Relationship(back_populates="club")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    club_id: str = Field(foreign_key="clubs.id")
    title: str
    description: Optional[str] = None
    location: Optional[str] = None

    start_time: datetime
    end_time: Optional[datetime] = None

    number_of_courts: int = Field(default=1)
    max_participants: int = Field(default=20)
    court_cost_per_hour: Optional[float] = None
    total_court_cost: Optional[float] = None

    payment_type: str = Field(default="split")
    buffet_price: Optional[float] = None

    status: str = Field(default="upcoming")
    created_by: str = Field(foreign_key="users.id")

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    club: Optional["Club"] = Relationship(back_populates="sessions")
    matches: List["Match"] = Relationship(back_populates="session")


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    court_number: int = Field(default=1)

    match_type: str = Field(default="single")

    team_a_player_1_id: str = Field(foreign_key="users.id")
    team_a_player_2_id: Optional[str] = Field(foreign_key="users.id", default=None)
    team_a_score: Optional[int] = None

    team_b_player_1_id: str = Field(foreign_key="users.id")
    team_b_player_2_id: Optional[str] = Field(foreign_key="users.id", default=None)
    team_b_score: Optional[int] = None
    score: Optional[str] = None

    winner_team: Optional[str] = None

    set_scores: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))

    status: str = Field(default="scheduled")

    shuttlecocks_used: int = Field(default=0)
    shuttlecock_price: Optional[float] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc)

    session: Optional["Session"] = Relationship(back_populates="matches")


# ============= ADDITIONAL TABLES =============

class InboxMessage(SQLModel, table=True):
    __tablename__ = "inbox_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str
    message: str
    message_type: str = Field(default="notification")

    amount: Optional[float] = None
    qr_code_url: Optional[str] = None
    session_id: Optional[str] = Field(foreign_key="sessions.id", default=None)

    proof_image_url: Optional[str] = None
    proof_uploaded_at: Optional[datetime] = None
    proof_expires_at: Optional[datetime] = None

    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now_utc)


class Court(SQLModel, table=True):
    __tablename__ = "courts"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    court_number: int
    status: str = Field(default="available")
    auto_matching_enabled: bool = Field(default=True)
    current_match_id: Optional[str] = Field(foreign_key="matches.id", default=None)
    created_at: datetime = Field(default_factory=now_utc)
    closed_at: Optional[datetime] = None


class PreMatch(SQLModel, table=True):
    __tablename__ = "pre_matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    match_order: int = Field(default=1)

    team_a_player_1_id: str = Field(foreign_key="users.id")
    team_a_player_2_id: Optional[str] = Field(foreign_key="users.id", default=None)
    team_b_player_1_id: str = Field(foreign_key="users.id")
    team_b_player_2_id: Optional[str] = Field(foreign_key="users.id", default=None)

    status: str = Field(default="queued")
    created_at: datetime = Field(default_factory=now_utc)
    activated_at: Optional[datetime] = None
