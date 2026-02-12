'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface RatingPoint {
  date: string;
  rating: number;
  matches: number;
}

interface RatingTrendChartProps {
  data?: RatingPoint[];
  height?: number;
}

const defaultData: RatingPoint[] = [
  { date: 'Jan', rating: 1000, matches: 5 },
  { date: 'Feb', rating: 1025, matches: 8 },
  { date: 'Mar', rating: 1010, matches: 6 },
  { date: 'Apr', rating: 1045, matches: 10 },
  { date: 'May', rating: 1030, matches: 7 },
  { date: 'Jun', rating: 1060, matches: 12 },
];

export function RatingTrendChart({ data = defaultData, height = 250 }: RatingTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[250px] text-gray-400">
        ยังไม่มีข้อมูล
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="ratingGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="date" 
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
          domain={['dataMin - 50', 'dataMax + 50']}
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
            if (name === 'rating') return [value, 'Rating'];
            return [value, name];
          }}
          labelStyle={{ color: '#374151', fontWeight: 500 }}
        />
        <Area
          type="monotone"
          dataKey="rating"
          stroke="#3b82f6"
          strokeWidth={3}
          fill="url(#ratingGradient)"
          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
