import { useCallback, useEffect, useState } from 'react';
import { csrfHeaders } from '../../utils/csrfHeaders';

export type RelationshipIntelPanelProps = {
  personId: string;
  userTier: string;
};

const UPSELL_COPY_FALLBACK = 'Upgrade to Mid for AI-generated relationship insights.';

type Status = 'idle' | 'loading' | 'loaded' | 'error' | 'opted_out' | 'credit_exhausted';

type StayOrGoDirection = 'building' | 'stable' | 'fading';

type NarrativeData = {
  person_id: string;
  narrative?: string;
  stay_or_go?: {
    direction: StayOrGoDirection;
    explanation: string;
  };
  cost_narrative?: string;
  opted_out?: boolean;
};

function jsonAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('mingus_token') || '';
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function stayOrGoBadgeClass(direction: StayOrGoDirection): string {
  if (direction === 'building') {
    return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
  }
  if (direction === 'fading') {
    return 'bg-amber-500/15 text-amber-200 border-amber-500/30';
  }
  return 'bg-[#2a2030] text-[#9a8f7e] border-[#3d3344]';
}

function stayOrGoLabel(direction: StayOrGoDirection): string {
  if (direction === 'building') return 'Building';
  if (direction === 'fading') return 'Fading';
  return 'Stable';
}

function LoadingSpinner() {
  return (
    <div
      className="h-4 w-4 animate-spin rounded-full border-2 border-[#9a8f7e] border-t-transparent"
      aria-hidden
    />
  );
}

function ExcludedMessage() {
  return <p className="text-sm text-[#9a8f7e]">This person is excluded from AI insights.</p>;
}

export function RelationshipIntelPanel({ personId, userTier }: RelationshipIntelPanelProps) {
  const [status, setStatus] = useState<Status>('idle');
  const [data, setData] = useState<NarrativeData | null>(null);
  const [optingOut, setOptingOut] = useState(false);
  const [upsellCopy, setUpsellCopy] = useState(UPSELL_COPY_FALLBACK);
  const [upsellLoading, setUpsellLoading] = useState(userTier === 'budget');

  useEffect(() => {
    if (userTier !== 'budget') return;

    let cancelled = false;
    setUpsellLoading(true);

    void (async () => {
      try {
        const res = await fetch('/api/relationship-intelligence/upsell-copy', {
          method: 'GET',
          credentials: 'include',
          headers: jsonAuthHeaders(),
        });
        if (!res.ok) {
          throw new Error('upsell copy fetch failed');
        }
        const json = (await res.json()) as { copy?: string };
        if (!cancelled) {
          setUpsellCopy(json.copy?.trim() || UPSELL_COPY_FALLBACK);
        }
      } catch {
        if (!cancelled) {
          setUpsellCopy(UPSELL_COPY_FALLBACK);
        }
      } finally {
        if (!cancelled) {
          setUpsellLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [userTier]);

  const fetchInsight = useCallback(async () => {
    setStatus('loading');
    try {
      const res = await fetch('/api/relationship-intelligence/narrative', {
        method: 'POST',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({ person_id: personId }),
      });
      if (res.status === 402) {
        setStatus('credit_exhausted');
        return;
      }
      if (!res.ok) {
        setStatus('error');
        return;
      }
      const json = (await res.json()) as NarrativeData;
      if (json.opted_out) {
        setData(json);
        setStatus('opted_out');
        return;
      }
      setData(json);
      setStatus('loaded');
    } catch {
      setStatus('error');
    }
  }, [personId]);

  const handleOptOut = useCallback(async () => {
    if (optingOut || status === 'opted_out') return;
    setOptingOut(true);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({ llm_opt_out: true }),
      });
      if (!res.ok) {
        setOptingOut(false);
        return;
      }
      setData(null);
      setStatus('opted_out');
    } catch {
      setOptingOut(false);
    }
  }, [optingOut, personId, status]);

  if (userTier === 'budget') {
    return (
      <div className="mt-3 rounded-lg border border-[#2a2030] bg-[#1a1520]/60 px-3 py-3">
        {upsellLoading ? (
          <p className="text-sm text-[#9a8f7e]">Loading...</p>
        ) : (
          <p className="text-sm leading-relaxed text-[#9a8f7e]">{upsellCopy}</p>
        )}
      </div>
    );
  }

  if (status === 'opted_out') {
    return (
      <div className="mt-3">
        <ExcludedMessage />
      </div>
    );
  }

  if (status === 'idle') {
    return (
      <div className="mt-3">
        <button
          type="button"
          className="min-h-11 rounded-lg border border-[#3d3344] bg-[#1a1520] px-3 py-2 text-sm font-semibold text-[#A78BFA] transition hover:border-[#A78BFA]/40 hover:bg-[#241c2a] sm:min-h-0"
          onClick={() => void fetchInsight()}
        >
          Here are our thoughts
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="mt-3 flex items-center gap-2 text-sm text-[#9a8f7e]">
        <LoadingSpinner />
        <span>Loading insight…</span>
      </div>
    );
  }

  if (status === 'credit_exhausted') {
    return (
      <div className="mt-3 rounded-lg border border-amber-500/20 bg-[#1a1520]/60 px-3 py-3">
        <p className="text-sm font-semibold text-amber-200/90">Monthly insights used up</p>
        <p className="mt-2 text-sm leading-relaxed text-[#9a8f7e]">
          You&apos;ve used your 10 AI insights for this month. Upgrade to Pro for unlimited.
        </p>
        <span className="mt-3 inline-block text-xs font-semibold text-[#A78BFA] underline underline-offset-2">
          Learn about Pro
        </span>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="mt-3 space-y-2">
        <p className="text-sm text-[#9a8f7e]">Insight unavailable right now.</p>
        <button
          type="button"
          className="text-xs font-semibold text-[#A78BFA] underline underline-offset-2 hover:opacity-90"
          onClick={() => void fetchInsight()}
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-[#2a2030] bg-[#1a1520]/40 px-3 py-3">
      <div className="flex items-center justify-end">
        <button
          type="button"
          className="text-[10px] font-medium text-[#9a8f7e] underline underline-offset-2 hover:text-[#A78BFA]"
          onClick={() => void fetchInsight()}
        >
          Refresh
        </button>
      </div>

      {data?.narrative ? (
        <p className="text-sm leading-relaxed text-[#F0E8D8]">{data.narrative}</p>
      ) : null}

      {data?.stay_or_go ? (
        <div className="space-y-1.5">
          <span
            className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${stayOrGoBadgeClass(data.stay_or_go.direction)}`}
          >
            {stayOrGoLabel(data.stay_or_go.direction)}
          </span>
          <p className="text-sm text-[#F0E8D8]">{data.stay_or_go.explanation}</p>
        </div>
      ) : null}

      {data?.cost_narrative ? (
        <p className="text-xs italic text-[#9a8f7e]">{data.cost_narrative}</p>
      ) : null}

      <div className="border-t border-[#2a2030] pt-2">
        <button
          type="button"
          className="text-[10px] text-[#6b6156] underline underline-offset-2 hover:text-[#9a8f7e] disabled:opacity-50"
          disabled={optingOut}
          onClick={() => void handleOptOut()}
        >
          {optingOut ? 'Updating…' : 'Exclude from AI analysis'}
        </button>
      </div>

      <p className="text-[10px] text-[#6b6156]">
        AI observations based on your check-ins. Not clinical advice.
      </p>
    </div>
  );
}
