export const queryKeys = {
  me: ['me'] as const,
  clubs: ['clubs'] as const,
  club: (clubId: string) => ['club', clubId] as const,
  sessions: (clubId: string) => ['sessions', clubId] as const,
  session: (sessionId: string) => ['session', sessionId] as const,
  matches: (sessionId: string) => ['matches', sessionId] as const,
  match: (matchId: string) => ['match', matchId] as const,
  leaderboard: (clubId: string) => ['leaderboard', clubId] as const,
  clubStats: (clubId: string) => ['clubStats', clubId] as const,
};
