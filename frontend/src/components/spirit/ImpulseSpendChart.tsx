import React, { useId } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface ImpulseSpendPoint {
  week: string;
  practiceScore: number;
  impulseSpend: number | null;
}

export interface ImpulseSpendChartProps {
  data: ImpulseSpendPoint[];
}

const AMBER = '#C4A064';
const RED = '#DC2626';

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ImpulseSpendPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <div className="font-semibold text-slate-800">{p.week}</div>
      <div className="mt-1 text-slate-600">
        Impulse spend:{' '}
        <span className="font-medium text-[#0f172a]">
          {p.impulseSpend == null ? '—' : `$${Number(p.impulseSpend).toFixed(0)}`}
        </span>
      </div>
      <div className="text-slate-600">
        Practice score: <span className="font-medium text-[#0f172a]">{p.practiceScore.toFixed(1)}</span>
      </div>
    </div>
  );
}

export function ImpulseSpendChart({ data }: ImpulseSpendChartProps) {
  const uid = useId().replace(/:/g, '');
  const gradImpulse = `isc-impulse-${uid}`;

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
      <h3 className="mb-2 text-center text-sm font-semibold text-[#0f172a]">
        Impulse spend vs. practice
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
          <defs>
            <linearGradient id={gradImpulse} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={RED} stopOpacity={0.28} />
              <stop offset="100%" stopColor={RED} stopOpacity={0.02} />
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
            yAxisId="impulse"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            width={40}
            tickFormatter={(v) => `$${v}`}
          />
          <YAxis
            yAxisId="practice"
            orientation="right"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={28}
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            formatter={(value) => <span className="text-slate-600">{value}</span>}
          />
          <Area
            yAxisId="impulse"
            type="monotone"
            dataKey="impulseSpend"
            name="Impulse spend"
            stroke={RED}
            strokeWidth={2}
            fill={`url(#${gradImpulse})`}
            connectNulls={false}
          />
          <Line
            yAxisId="practice"
            type="monotone"
            dataKey="practiceScore"
            name="Practice score"
            stroke={AMBER}
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            activeDot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
