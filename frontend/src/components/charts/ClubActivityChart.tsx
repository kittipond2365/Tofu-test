'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ActivityData {
  date: string;
  sessions: number;
  participants: number;
  matches: number;
}

interface ClubActivityChartProps {
  data: ActivityData[];
  height?: number;
}

export function ClubActivityChart({ data, height = 280 }: ClubActivityChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[280px] text-gray-400">
        ยังไม่มีข้อมูล
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="sessionsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="participantsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="matchesGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="date" 
          stroke="#9ca3af" 
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          stroke="#9ca3af" 
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }}
          formatter={(value: any, name: any) => {
            const labels: Record<string, string> = {
              sessions: 'กิจกรรม',
              participants: 'ผู้เข้าร่วม',
              matches: 'แมทช์'
            };
            return [value, labels[name] || name];
          }}
          labelStyle={{ color: '#374151', fontWeight: 500 }}
        />
        <Legend 
          wrapperStyle={{ paddingTop: '10px' }}
          formatter={(value: string) => {
            const labels: Record<string, string> = {
              sessions: 'กิจกรรม',
              participants: 'ผู้เข้าร่วม',
              matches: 'แมทช์'
            };
            return labels[value] || value;
          }}
        />
        <Area
          type="monotone"
          dataKey="sessions"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#sessionsGradient)"
        />
        <Area
          type="monotone"
          dataKey="participants"
          stroke="#10b981"
          strokeWidth={2}
          fill="url(#participantsGradient)"
        />
        <Area
          type="monotone"
          dataKey="matches"
          stroke="#f59e0b"
          strokeWidth={2}
          fill="url(#matchesGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
