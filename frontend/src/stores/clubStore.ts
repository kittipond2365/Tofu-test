import { create } from 'zustand';
interface ClubState { currentClub: string | null; setCurrentClub: (clubId: string | null) => void; }
export const useClubStore = create<ClubState>((set) => ({ currentClub: null, setCurrentClub: (currentClub) => set({ currentClub }) }));
