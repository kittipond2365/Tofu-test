import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';
import type { ClubDetailResponse, ClubResponse, ClubStatsResponse, MatchResponse, PlayerStatsResponse, SessionDetailResponse, SessionResponse, TokenResponse, UserResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
export const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async (): Promise<string | null> => {
  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
    const { access_token, refresh_token } = response.data as TokenResponse;
    setTokens(access_token, refresh_token);
    return access_token;
  } catch {
    logout();
    return null;
  }
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error?.response?.status;

    const isAuthRoute = originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/refresh');

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = refreshAccessToken().finally(() => {
          isRefreshing = false;
        });
      }

      const newToken = await refreshPromise;
      if (newToken) {
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export const apiClient = {
  baseURL: API_URL,

  login: async (credentials: { email: string; password: string }): Promise<TokenResponse> => (await api.post('/auth/login', credentials)).data,
  register: async (data: { email: string; password: string; full_name: string; display_name?: string; phone?: string; picture_url?: string }): Promise<UserResponse> => (await api.post('/auth/register', data)).data,
  getMe: async (): Promise<UserResponse> => (await api.get('/auth/me')).data,
  getMeWithToken: async (token: string): Promise<UserResponse> => {
    const response = await axios.get(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  getClubs: async (): Promise<ClubResponse[]> => (await api.get('/clubs')).data,
  getClub: async (clubId: string): Promise<ClubDetailResponse> => (await api.get(`/clubs/${clubId}`)).data,
  createClub: async (data: { name: string; slug: string; description?: string; location?: string; max_members?: number; is_public?: boolean }): Promise<ClubResponse> => (await api.post('/clubs', data)).data,
  joinClub: async (clubId: string): Promise<void> => { await api.post(`/clubs/${clubId}/join`); },

  getSessions: async (clubId: string): Promise<SessionResponse[]> => (await api.get(`/clubs/${clubId}/sessions`)).data,
  getSession: async (sessionId: string): Promise<SessionDetailResponse> => {
    const session = (await api.get(`/sessions/${sessionId}`)).data as SessionDetailResponse;
    const registrations = (await api.get(`/sessions/${sessionId}/registrations`)).data;
    return { ...session, registrations };
  },
  createSession: async (clubId: string, data: { title: string; description?: string; location: string; start_time: string; end_time: string; max_participants: number }): Promise<SessionResponse> => (await api.post(`/clubs/${clubId}/sessions`, data)).data,
  openRegistration: async (sessionId: string): Promise<void> => { await api.post(`/sessions/${sessionId}/open`); },

  registerForSession: async (sessionId: string): Promise<void> => { await api.post(`/sessions/${sessionId}/register`); },
  cancelRegistration: async (sessionId: string): Promise<void> => { await api.post(`/sessions/${sessionId}/cancel`); },
  checkIn: async (sessionId: string): Promise<void> => { await api.post(`/sessions/${sessionId}/checkin`); },
  checkOut: async (sessionId: string): Promise<void> => { await api.post(`/sessions/${sessionId}/checkout`); },

  getMatches: async (sessionId: string): Promise<MatchResponse[]> => (await api.get(`/sessions/${sessionId}/matches`)).data,
  getMatch: async (matchId: string): Promise<MatchResponse> => (await api.get(`/matches/${matchId}`)).data,
  createMatch: async (sessionId: string, data?: { court_number?: number; team_a_player_1_id: string; team_a_player_2_id?: string; team_b_player_1_id: string; team_b_player_2_id?: string }): Promise<MatchResponse> => (await api.post(`/sessions/${sessionId}/matches`, data)).data,
  updateScore: async (matchId: string, score: { score: string; winner_team: 'A' | 'B' }): Promise<void> => { await api.patch(`/matches/${matchId}/score`, score); },
  startMatch: async (matchId: string): Promise<void> => { await api.post(`/matches/${matchId}/start`); },
  completeMatch: async (matchId: string, winner: 'A' | 'B'): Promise<void> => { await api.post(`/matches/${matchId}/complete`, null, { params: { winner_team: winner } }); },

  getClubStats: async (clubId: string): Promise<ClubStatsResponse> => (await api.get(`/clubs/${clubId}/stats`)).data,
  getLeaderboard: async (clubId: string): Promise<PlayerStatsResponse[]> => (await api.get(`/clubs/${clubId}/leaderboard`)).data,
  getUserStats: async (userId: string): Promise<PlayerStatsResponse> => (await api.get(`/users/${userId}/stats`)).data,

  // Profile
  updateProfile: async (data: { display_name?: string; full_name?: string; email?: string; phone?: string }): Promise<UserResponse> => (await api.patch('/auth/me', data)).data,
};
