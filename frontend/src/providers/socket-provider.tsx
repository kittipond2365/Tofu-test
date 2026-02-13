"use client";
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { connectSocket, disconnectSocket } from '@/lib/socket';

export default function SocketProvider() {
  const qc = useQueryClient();
  useEffect(() => {
    try {
      const s = connectSocket();
      s.on('registration_updated', (payload) => {
        if (payload?.session_id) qc.invalidateQueries({ queryKey: ['session', payload.session_id] });
      });
      s.on('match_updated', () => {
        qc.invalidateQueries({ queryKey: ['matches'] });
      });
      s.on('score_updated', (payload) => {
        if (payload?.match_id) qc.invalidateQueries({ queryKey: ['match', payload.match_id] });
      });
      s.on('player_joined', (payload) => {
        if (payload?.session_id) qc.invalidateQueries({ queryKey: ['session', payload.session_id] });
      });
      s.on('player_left', (payload) => {
        if (payload?.session_id) qc.invalidateQueries({ queryKey: ['session', payload.session_id] });
      });
      s.on('connect_error', (err) => {
        console.warn('Socket connection error:', err.message);
      });
      return () => disconnectSocket();
    } catch (err) {
      console.warn('Failed to initialize socket:', err);
    }
  }, [qc]);
  return null;
}
