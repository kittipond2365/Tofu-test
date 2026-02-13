from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index, Column, JSON

# ============= LINK TABLES (No relationships, just FKs) =============

class ClubMember(SQLModel, table=True):
    __tablename__ = "club_members"
    
    club_id: int = Field(foreign_key="clubs.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class ClubModerator(SQLModel, table=True):
    __tablename__ = "club_moderators"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id")
    user_id: int = Field(foreign_key="users.id")
    appointed_by: int = Field(foreign_key="users.id")
    appointed_at: datetime = Field(default_factory=datetime.utcnow)

class SessionRegistration(SQLModel, table=True):
    __tablename__ = "session_registrations"
    
    session_id: int = Field(foreign_key="sessions.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="confirmed")  # confirmed, cancelled, attended

# ============= MAIN MODELS =============

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    line_user_id: str = Field(unique=True, index=True)
    display_name: str
    picture_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_super_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Clubs owned (via owner_id FK in Club)
    owned_clubs: List["Club"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )

class Club(SQLModel, table=True):
    __tablename__ = "clubs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
    location: Optional[str] = None
    max_members: int = Field(default=100)
    is_public: bool = Field(default=True)
    invite_code: Optional[str] = None
    invite_qr_url: Optional[str] = None
    
    # Owner
    owner_id: int = Field(foreign_key="users.id")
    
    # Verification
    is_verified: bool = Field(default=False)
    verified_by: Optional[int] = Field(foreign_key="users.id", default=None)
    verified_at: Optional[datetime] = None
    
    # Ownership transfer
    previous_owner_id: Optional[int] = Field(foreign_key="users.id", default=None)
    transferred_at: Optional[datetime] = None
    
    # QR Payment
    payment_qr_url: Optional[str] = None
    payment_method_note: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    owner: Optional["User"] = Relationship(
        back_populates="owned_clubs",
        sa_relationship_kwargs={"foreign_keys": "Club.owner_id"}
    )
    sessions: List["Session"] = Relationship(back_populates="club")

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="clubs.id")
    title: str
    description: Optional[str] = None
    
    # Session time
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Court info
    number_of_courts: int = Field(default=1)
    court_cost_per_hour: Optional[float] = None
    total_court_cost: Optional[float] = None
    
    # Payment settings
    payment_type: str = Field(default="split")  # split, per_shuttle, buffet
    buffet_price: Optional[float] = None  # For buffet type
    
    # Status
    status: str = Field(default="upcoming")  # upcoming, active, completed, cancelled
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    club: Optional["Club"] = Relationship(back_populates="sessions")
    matches: List["Match"] = Relationship(back_populates="session")

class Match(SQLModel, table=True):
    __tablename__ = "matches"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    court_number: int = Field(default=1)
    
    # Match type
    match_type: str = Field(default="single")  # single, bo2, bo3
    
    # Team A
    team_a_player_1_id: int = Field(foreign_key="users.id")
    team_a_player_2_id: Optional[int] = Field(foreign_key="users.id", default=None)
    team_a_score: Optional[int] = None
    
    # Team B
    team_b_player_1_id: int = Field(foreign_key="users.id")
    team_b_player_2_id: Optional[int] = Field(foreign_key="users.id", default=None)
    team_b_score: Optional[int] = None
    
    # Results
    winner_team: Optional[str] = None  # "A", "B", or "draw"
    
    # For BO2/BO3
    set_scores: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))  # JSON: {"set1": {"A": 21, "B": 18}, ...}
    
    # Status
    status: str = Field(default="scheduled")  # scheduled, in_progress, completed, cancelled
    
    # Shuttlecock usage
    shuttlecocks_used: int = Field(default=0)
    shuttlecock_price: Optional[float] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: Optional["Session"] = Relationship(back_populates="matches")

# ============= ADDITIONAL TABLES =============

class InboxMessage(SQLModel, table=True):
    __tablename__ = "inbox_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str
    message: str
    message_type: str = Field(default="notification")  # payment, notification, invite, result
    
    # For payment messages
    amount: Optional[float] = None
    qr_code_url: Optional[str] = None
    session_id: Optional[int] = Field(foreign_key="sessions.id", default=None)
    
    # For payment proof
    proof_image_url: Optional[str] = None
    proof_uploaded_at: Optional[datetime] = None
    proof_expires_at: Optional[datetime] = None
    
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Court(SQLModel, table=True):
    __tablename__ = "courts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    court_number: int
    status: str = Field(default="available")  # available, occupied, maintenance, closed
    auto_matching_enabled: bool = Field(default=True)
    current_match_id: Optional[int] = Field(foreign_key="matches.id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

class PreMatch(SQLModel, table=True):
    __tablename__ = "pre_matches"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    match_order: int = Field(default=1)
    
    # Players
    team_a_player_1_id: int = Field(foreign_key="users.id")
    team_a_player_2_id: Optional[int] = Field(foreign_key="users.id", default=None)
    team_b_player_1_id: int = Field(foreign_key="users.id")
    team_b_player_2_id: Optional[int] = Field(foreign_key="users.id", default=None)
    
    status: str = Field(default="queued")  # queued, on_deck, active, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
