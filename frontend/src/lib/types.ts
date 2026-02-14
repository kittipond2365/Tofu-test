export type UserRole = 'owner' | 'moderator' | 'admin' | 'organizer' | 'member';
export type SessionStatus = 'draft' | 'upcoming' | 'open' | 'full' | 'active' | 'ongoing' | 'completed' | 'cancelled';
export type RegistrationStatus = 'confirmed' | 'waitlisted' | 'cancelled' | 'attended' | 'no_show';
export type MatchStatus = 'scheduled' | 'ongoing' | 'completed' | 'cancelled';

export interface TokenResponse { access_token: string; refresh_token: string; token_type: string; expires_in: number; }
export interface UserResponse { id: string; email: string; full_name: string; display_name?: string; phone?: string; avatar_url?: string; total_matches: number; wins: number; losses: number; rating: number; is_active: boolean; created_at: string; }
export interface ClubResponse { id: string; name: string; slug: string; description?: string; location?: string; max_members: number; is_public: boolean; created_at: string; member_count: number; }
export interface ClubMemberResponse { id: string; user_id: string; role: UserRole; full_name: string; display_name?: string; avatar_url?: string; matches_in_club: number; rating_in_club: number; joined_at: string; }
export interface ClubDetailResponse extends ClubResponse { members: ClubMemberResponse[]; }
export interface SessionResponse { id: string; club_id: string; title: string; description?: string; location: string; start_time: string; end_time: string; max_participants: number; status: SessionStatus; created_by: string; created_at: string; confirmed_count: number; waitlist_count: number; participant_count?: number; }
export interface SessionDetailResponse extends SessionResponse { registrations: SessionRegistrationResponse[]; }
export interface SessionRegistrationResponse { id: string; user_id: string; full_name: string; display_name?: string; status: RegistrationStatus; waitlist_position?: number; checked_in_at?: string; checked_out_at?: string; registered_at: string; }
export interface PlayerSummary { id: string; full_name: string; display_name?: string; avatar_url?: string; rating: number; }
export interface MatchResponse { id: string; session_id: string; court_number: number; team_a_player_1: PlayerSummary; team_a_player_2?: PlayerSummary; team_b_player_1: PlayerSummary; team_b_player_2?: PlayerSummary; score?: string; winner_team?: string; status: MatchStatus; started_at?: string; completed_at?: string; created_at: string; }
export interface RatingHistoryPoint { date: string; rating: number; matches: number; }
export interface MatchesPerMonthPoint { month: string; matches: number; }
export interface PlayerStatsResponse { user_id: string; full_name: string; display_name?: string; avatar_url?: string; total_matches: number; wins: number; losses: number; win_rate: number; rating: number; matches_this_month: number; rating_history?: RatingHistoryPoint[]; matches_per_month?: MatchesPerMonthPoint[]; }
export interface ActivityDataPoint { date: string; sessions: number; participants: number; matches: number; }

export interface ClubStatsResponse { club_id: string; club_name: string; total_members: number; total_sessions: number; total_matches: number; top_players: PlayerStatsResponse[]; recent_sessions: SessionResponse[]; activity_data?: ActivityDataPoint[]; }
