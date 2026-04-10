import React, { useId } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface PracticeVsSavingsPoint {
  week: string;
  practiceScore: number;
  savingsRate: number | null;
}

export interface PracticeVsSavingsChartProps {
  data: PracticeVsSavingsPoint[];
}

const AMBER = '#C4A064';
const GREEN = '#2A7A52';

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: PracticeVsSavingsPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <div className="font-semibold text-slate-800">{p.week}</div>
      <div className="mt-1 text-slate-600">
        Practice score: <span className="font-medium text-[#0f172a]">{p.practiceScore.toFixed(1)}</span>
      </div>
      <div className="text-slate-600">
        Savings rate:{' '}
        <span className="font-medium text-[#0f172a]">
          {p.savingsRate == null ? '—' : `${(p.savingsRate * 100).toFixed(1)}%`}
        </span>
      </div>
    </div>
  );
}

export function PracticeVsSavingsChart({ data }: PracticeVsSavingsChartProps) {
  const uid = useId().replace(/:/g, '');
  const gradPractice = `pvsc-practice-${uid}`;
  const gradSavings = `pvsc-savings-${uid}`;

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
      <h3 className="mb-2 text-center text-sm font-semibold text-[#0f172a]">
        Practice score vs. savings rate
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
          <defs>
            <linearGradient id={gradPractice} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={AMBER} stopOpacity={0.35} />
              <stop offset="100%" stopColor={AMBER} stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id={gradSavings} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={GREEN} stopOpacity={0.35} />
              <stop offset="100%" stopColor={GREEN} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#E8E4DC" strokeDasharray="3 3" />
          <XAxis
            dataKey="week"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            yAxisId="practice"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            width={40}
          />
          <YAxis
            yAxisId="savings"
            orientation="right"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            width={44}
            tickFormatter={(v) => `${Math.round(Number(v) * 100)}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={28}
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            formatter={(value) => <span className="text-slate-600">{value}</span>}
          />
          <Area
            yAxisId="practice"
            type="monotone"
            dataKey="practiceScore"
            name="Practice score"
            stroke={AMBER}
            strokeWidth={2}
            fill={`url(#${gradPractice})`}
            connectNulls
          />
          <Area
            yAxisId="savings"
            type="monotone"
            dataKey="savingsRate"
            name="Savings rate"
            stroke={GREEN}
            strokeWidth={2}
            fill={`url(#${gradSavings})`}
            connectNulls={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
