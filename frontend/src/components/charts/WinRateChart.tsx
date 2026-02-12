'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface WinRateChartProps {
  wins: number;
  losses: number;
  size?: number;
}

const COLORS = ['#22c55e', '#ef4444'];

export function WinRateChart({ wins, losses, size = 200 }: WinRateChartProps) {
  const data = [
    { name: 'ชนะ', value: wins || 0 },
    { name: 'แพ้', value: losses || 0 },
  ];

  const total = wins + losses;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : '0.0';

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <div className="text-gray-400 text-sm">ยังไม่มีข้อมูล</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width={size} height={size}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={size * 0.3}
            outerRadius={size * 0.45}
            paddingAngle={2}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '8px 12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(value: any, name: any) => [value, name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-2 text-center">
        <span className="text-2xl font-bold text-gradient">{winRate}%</span>
        <p className="text-xs text-gray-500">อัตราชนะ</p>
      </div>
    </div>
  );
}
