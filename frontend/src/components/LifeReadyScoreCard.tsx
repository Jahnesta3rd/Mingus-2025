import React, { useEffect, useState, useCallback } from 'react';

interface LifeReadyScoreComponent {
  score: number;
  weight: number;
}

export interface LifeReadyScoreApiResponse {
  life_ready_score: number;
  components: {
    vibe: LifeReadyScoreComponent;
    body: LifeReadyScoreComponent;
    wellness: LifeReadyScoreComponent;
    financial: LifeReadyScoreComponent;
    stability: LifeReadyScoreComponent;
  };
  trend: 'improving' | 'declining' | 'stable';
  headline: string;
}

function authHeadersGet(): HeadersInit {
  const token = localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
  const h: Record<string, string> = {};
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

const COMPONENT_ORDER = ['vibe', 'body', 'wellness', 'financial', 'stability'] as const;
type ComponentKey = (typeof COMPONENT_ORDER)[number];

const LABELS: Record<ComponentKey, string> = {
  vibe: 'Vibe',
  body: 'Body',
  wellness: 'Wellness',
  financial: 'Financial',
  stability: 'Stability',
};

function weightedBarPercent(score: number, weight: number): number {
  const v = score * weight;
  return Math.max(0, Math.min(100, v));
}

function ScoreRingSkeleton() {
  return (
    <div className="flex flex-col items-center">
      <div
        className="h-44 w-44 rounded-full border-[10px] border-[#E2E8F0] bg-[#F8FAFC] animate-pulse"
        aria-hidden
      />
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 62;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = c * (1 - clamped / 100);
  return (
    <div className="relative mx-auto flex h-44 w-44 items-center justify-center">
      <svg className="h-44 w-44 -rotate-90" viewBox="0 0 144 144" aria-hidden>
        <circle
          cx="72"
          cy="72"
          r={r}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth="10"
        />
        <circle
          cx="72"
          cy="72"
          r={r}
          fill="none"
          stroke="#5B2D8E"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold tabular-nums text-[#1E293B]" aria-label={`Life ready score ${clamped} out of 100`}>
          {clamped}
        </span>
      </div>
    </div>
  );
}

function TrendIndicator({ trend }: { trend: LifeReadyScoreApiResponse['trend'] }) {
  if (trend === 'improving') {
    return <span className="text-xl font-semibold text-[#059669]" aria-label="Trending up">↑</span>;
  }
  if (trend === 'declining') {
    return <span className="text-xl font-semibold text-[#DC2626]" aria-label="Trending down">↓</span>;
  }
  return <span className="text-xl font-semibold text-[#64748B]" aria-label="Stable">—</span>;
}

export default function LifeReadyScoreCard() {
  const [data, setData] = useState<LifeReadyScoreApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/life-ready-score', {
        credentials: 'include',
        headers: authHeadersGet(),
      });
      if (!res.ok) {
        throw new Error('Failed to load Life Ready Score');
      }
      const json = (await res.json()) as LifeReadyScoreApiResponse;
      setData(json);
    } catch {
      setData(null);
      setError('Unable to load score');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="rounded-2xl bg-white p-6 shadow-md">
      {loading ? (
        <div className="flex flex-col items-center">
          <ScoreRingSkeleton />
          <p className="mt-4 h-4 w-40 animate-pulse rounded bg-[#E2E8F0]" />
          <div className="mt-4 flex w-full max-w-xs flex-col gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-2 w-full animate-pulse rounded-full bg-[#E2E8F0]" />
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center gap-4 py-6 text-center">
          <p className="text-sm text-[#64748B]">{error}</p>
          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#5B2D8E] px-5 text-sm font-medium text-white hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Retry
          </button>
        </div>
      ) : data ? (
        <div className="flex flex-col items-center">
          <ScoreRing score={data.life_ready_score} />
          <h2 className="mt-2 text-center text-lg font-semibold text-[#1E293B]">Life Ready Score</h2>
          <div className="mt-1 flex min-h-8 items-center justify-center">
            <TrendIndicator trend={data.trend} />
          </div>
          <p className="mt-1 max-w-md text-center text-sm italic text-[#64748B]">{data.headline}</p>
          <div className="mt-6 w-full max-w-sm space-y-3">
            {COMPONENT_ORDER.map((key) => {
              const comp = data.components[key];
              const pct = weightedBarPercent(comp.score, comp.weight);
              return (
                <div key={key}>
                  <div className="mb-1 flex justify-between text-sm text-[#1E293B]">
                    <span>{LABELS[key]}</span>
                    <span className="text-[#64748B]">{Math.round(comp.weight * 100)}% weight</span>
                  </div>
                  <svg
                    className="h-2 w-full overflow-hidden rounded-full"
                    viewBox="0 0 100 4"
                    preserveAspectRatio="none"
                    aria-hidden
                  >
                    <rect x="0" y="0" width="100" height="4" rx="2" fill="#E2E8F0" />
                    <rect x="0" y="0" width={pct} height="4" rx="2" fill="#7C3AED" />
                  </svg>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}
