import { create } from 'zustand';
import type { SessionRegistrationResponse } from '@/lib/types';
interface SessionState { currentSession: string | null; registrations: SessionRegistrationResponse[]; setCurrentSession: (id: string | null) => void; setRegistrations: (r: SessionRegistrationResponse[]) => void; }
export const useSessionStore = create<SessionState>((set) => ({ currentSession: null, registrations: [], setCurrentSession: (currentSession) => set({ currentSession }), setRegistrations: (registrations) => set({ registrations }) }));
