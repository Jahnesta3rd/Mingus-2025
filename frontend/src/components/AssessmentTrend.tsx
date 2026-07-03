import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface HistoryPoint {
  created_at: string;
  score: number | null;
}

interface AssessmentTrendProps {
  assessmentType: string;
  history: HistoryPoint[];
}

export function AssessmentTrend({ history }: AssessmentTrendProps) {
  if (!history || history.length < 2) {
    return (
      <p className="text-sm text-[#64748B]">
        Only one assessment recorded. Take another to see your trend.
      </p>
    );
  }

  const data = [...history]
    .reverse()
    .filter((a) => a.score != null)
    .map((a) => ({
      date: new Date(a.created_at).toLocaleDateString(),
      score: a.score as number,
    }));

  if (data.length < 2) {
    return (
      <p className="text-sm text-[#64748B]">
        Only one scored assessment recorded. Take another to see your trend.
      </p>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey="score" stroke="#5B2D8E" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
