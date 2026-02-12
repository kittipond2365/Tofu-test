# Badminton Club Management - Frontend

Next.js 14 application with App Router for Badminton Club Management.

## Tech Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query (server state)
- Zustand (client state)
- Socket.io (real-time)
- Axios (API calls)

## Project Structure
```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth group routes
│   ├── clubs/             # Club pages
│   ├── sessions/          # Session pages
│   ├── matches/           # Match pages
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── ui/               # UI components
│   ├── forms/            # Form components
│   └── layouts/          # Layout components
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   ├── socket.ts         # Socket.io client
│   └── utils.ts          # Helper functions
├── hooks/                 # Custom hooks
├── store/                 # Zustand stores
└── types/                 # TypeScript types
```

## Getting Started

```bash
npm install
npm run dev
```

Open http://localhost:3000
