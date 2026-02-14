'use client';

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';

interface PlayerStats {
  category: string;
  value: number;
  fullMark: number;
}

interface PlayerStatsRadarProps {
  data: PlayerStats[];
  height?: number;
  playerName?: string;
}

export function PlayerStatsRadar({ 
  data, 
  height = 300,
  playerName 
}: PlayerStatsRadarProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-gray-400">
        ยังไม่มีข้อมูล
      </div>
    );
  }

  return (
    <div className="w-full">
      {playerName && (
        <h4 className="text-center text-sm font-medium text-gray-700 mb-2">
          {playerName}
        </h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis 
            dataKey="category" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Stats"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="#3b82f6"
            fillOpacity={0.3}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(value: any) => [`${value}/100`, 'คะแนน']}
            labelStyle={{ color: '#374151', fontWeight: 500 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
