from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    MEMBER = "member"


class SessionStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    FULL = "full"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RegistrationStatus(str, Enum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============= User Schemas =============
class UserBase(BaseModel):
    email: Optional[EmailStr] = None  # Optional for LINE users
    full_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)  # Optional for LINE users


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: str
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    rating: float = 1000.0
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # minutes


# ============= Club Schemas =============
class ClubBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    location: Optional[str] = None
    max_members: int = Field(default=100, ge=1, le=1000)
    is_public: bool = False


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1, le=1000)
    is_public: Optional[bool] = None


class ClubMemberResponse(BaseModel):
    id: str
    user_id: str
    role: UserRole
    full_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    matches_in_club: int
    rating_in_club: float
    joined_at: datetime
    
    class Config:
        from_attributes = True


class ClubResponse(ClubBase):
    id: str
    owner_id: Optional[str] = None
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    member_count: int = 0
    
    class Config:
        from_attributes = True


class ClubDetailResponse(ClubResponse):
    members: List[ClubMemberResponse] = []
    
    class Config:
        from_attributes = True


# ============= Session Schemas =============
class SessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: str = Field(..., min_length=1, max_length=500)
    start_time: datetime
    end_time: datetime
    max_participants: int = Field(default=20, ge=1, le=100)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[SessionStatus] = None


class SessionRegistrationResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    status: RegistrationStatus
    waitlist_position: Optional[int]
    checked_in_at: Optional[datetime]
    registered_at: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(SessionBase):
    id: str
    club_id: str
    status: SessionStatus
    created_by: str
    created_at: datetime
    confirmed_count: int = 0
    waitlist_count: int = 0
    
    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    registrations: List[SessionRegistrationResponse] = []
    
    class Config:
        from_attributes = True


# ============= Match Schemas =============
class MatchBase(BaseModel):
    court_number: int = Field(default=1, ge=1, le=20)
    team_a_player_1_id: str
    team_a_player_2_id: Optional[str] = None
    team_b_player_1_id: str
    team_b_player_2_id: Optional[str] = None


class MatchCreate(MatchBase):
    pass


class MatchUpdateScore(BaseModel):
    score: str = Field(..., pattern=r'^(\d+-\d+,?)+$')  # e.g., "21-19,18-21,21-15"
    winner_team: str = Field(..., pattern=r'^[AB]$')


class MatchUpdateStatus(BaseModel):
    status: MatchStatus


class PlayerSummary(BaseModel):
    id: str
    full_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    rating: float


class MatchResponse(BaseModel):
    id: str
    session_id: str
    court_number: int
    team_a_player_1: PlayerSummary
    team_a_player_2: Optional[PlayerSummary]
    team_b_player_1: PlayerSummary
    team_b_player_2: Optional[PlayerSummary]
    score: Optional[str]
    winner_team: Optional[str]
    status: MatchStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Registration Schemas =============
class RegistrationCreate(BaseModel):
    pass  # No fields needed, user_id from token


class CheckInOutRequest(BaseModel):
    user_id: str  # For admin/organizer to check in others
    action: str = Field(..., pattern=r'^(checkin|checkout)$')


# ============= Stats Schemas =============
class RatingHistoryPoint(BaseModel):
    date: str
    rating: float
    matches: int

class MatchesPerMonthPoint(BaseModel):
    month: str
    matches: int

class PlayerStatsResponse(BaseModel):
    user_id: str
    full_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    total_matches: int
    wins: int
    losses: int
    win_rate: float  # percentage
    rating: float
    matches_this_month: int = 0
    rating_history: List[RatingHistoryPoint] = []
    matches_per_month: List[MatchesPerMonthPoint] = []


class ClubStatsResponse(BaseModel):
    club_id: str
    club_name: str
    total_members: int
    total_sessions: int
    total_matches: int
    top_players: List[PlayerStatsResponse] = []
    recent_sessions: List[SessionResponse] = []
