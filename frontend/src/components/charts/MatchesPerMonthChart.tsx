'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface MonthData {
  month: string;
  matches: number;
}

interface MatchesPerMonthChartProps {
  data: MonthData[];
  height?: number;
}

export function MatchesPerMonthChart({ data, height = 250 }: MatchesPerMonthChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[250px] text-gray-400">
        ยังไม่มีข้อมูล
      </div>
    );
  }

  const maxMatches = Math.max(...data.map(d => d.matches));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="month" 
          stroke="#9ca3af" 
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          stroke="#9ca3af" 
          fontSize={12}
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
          formatter={(value: any) => [`${value} แมทช์`, 'จำนวนแมทช์']}
          labelStyle={{ color: '#374151', fontWeight: 500 }}
        />
        <Bar 
          dataKey="matches" 
          radius={[6, 6, 0, 0]}
          maxBarSize={40}
        >
          {data.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.matches === maxMatches ? '#3b82f6' : '#93c5fd'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
