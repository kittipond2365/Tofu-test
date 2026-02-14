import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;
export const connectSocket = () => {
  if (socket) return socket;
  const ws = process.env.NEXT_PUBLIC_WS_URL || '/ws';
  socket = io(ws, { transports: ['websocket'] });
  return socket;
};
export const getSocket = () => socket;
export const disconnectSocket = () => { socket?.disconnect(); socket = null; };
