import { useCallback, useState } from 'react';

export type RelationshipIntelPanelProps = {
  personId: string;
  userTier: string;
  llmOptOut: boolean;
};

type StayOrGoDirection = 'building' | 'fading' | 'stable';

type NarrativeResponse = {
  narrative?: string;
  stay_or_go?: {
    direction: StayOrGoDirection;
    explanation: string;
  };
  cost_narrative?: string;
};

type PanelState = 'idle' | 'loading' | 'loaded' | 'error' | 'opted_out';

function hasNarrativeContent(data: NarrativeResponse): boolean {
  if (data.narrative?.trim()) return true;
  if (data.stay_or_go?.direction && data.stay_or_go.explanation?.trim()) return true;
  if (data.cost_narrative?.trim()) return true;
  return false;
}

function directionChipClass(direction: StayOrGoDirection): string {
  if (direction === 'building') {
    return 'text-green-400 bg-green-400/10 rounded-full px-2 py-0.5 text-xs';
  }
  if (direction === 'fading') {
    return 'text-red-400 bg-red-400/10 rounded-full px-2 py-0.5 text-xs';
  }
  return 'text-amber-400 bg-amber-400/10 rounded-full px-2 py-0.5 text-xs';
}

function Disclaimer() {
  return (
    <p className="text-xs text-gray-400 mt-2">
      AI observations based on your check-ins. Not clinical advice.
    </p>
  );
}

function OptedOutMessage() {
  return (
    <p className="text-sm text-gray-500 italic">This person is excluded from AI insights.</p>
  );
}

export function RelationshipIntelPanel({
  personId,
  userTier,
  llmOptOut,
}: RelationshipIntelPanelProps) {
  const [optedOut, setOptedOut] = useState(llmOptOut);
  const [status, setStatus] = useState<PanelState>(llmOptOut ? 'opted_out' : 'idle');
  const [data, setData] = useState<NarrativeResponse | null>(null);
  const [optingOut, setOptingOut] = useState(false);

  const fetchInsight = useCallback(async () => {
    setStatus('loading');
    try {
      const res = await fetch('/api/relationship-intelligence/narrative', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_id: personId }),
      });
      if (!res.ok) {
        setData(null);
        setStatus('error');
        return;
      }
      const json = (await res.json()) as NarrativeResponse;
      if (!hasNarrativeContent(json)) {
        setData(null);
        setStatus('error');
        return;
      }
      setData(json);
      setStatus('loaded');
    } catch {
      setData(null);
      setStatus('error');
    }
  }, [personId]);

  const handleOptOut = useCallback(async () => {
    if (optingOut) return;
    setOptingOut(true);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ llm_opt_out: true }),
      });
      if (!res.ok) {
        setOptingOut(false);
        return;
      }
      setData(null);
      setOptedOut(true);
      setStatus('opted_out');
    } catch {
      setOptingOut(false);
    }
  }, [optingOut, personId]);

  if (optedOut || status === 'opted_out') {
    return (
      <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
        <OptedOutMessage />
      </div>
    );
  }

  if (userTier === 'budget') {
    return (
      <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
        <p className="text-sm text-gray-400 italic">
          Upgrade to Mid to see an AI read on this relationship.
        </p>
      </div>
    );
  }

  if (status === 'idle') {
    return (
      <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
        <button
          type="button"
          className="text-xs border border-amber-400/60 text-amber-400 rounded-full px-3 py-1 hover:bg-amber-400/10 transition"
          onClick={() => void fetchInsight()}
        >
          See AI insight
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
        <div
          className="animate-spin h-4 w-4 border-2 border-amber-400 border-t-transparent rounded-full"
          aria-hidden
        />
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
        <p className="text-sm text-gray-200">Insight unavailable right now.</p>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
      {data?.narrative ? (
        <p className="text-sm text-gray-200">{data.narrative}</p>
      ) : null}

      {data?.stay_or_go ? (
        <div className="mt-2">
          <span className={directionChipClass(data.stay_or_go.direction)}>
            {data.stay_or_go.direction}
          </span>
          {data.stay_or_go.explanation ? (
            <p className="text-sm text-gray-300 mt-1">{data.stay_or_go.explanation}</p>
          ) : null}
        </div>
      ) : null}

      {data?.cost_narrative ? (
        <p className="text-xs text-gray-400 mt-2 italic">{data.cost_narrative}</p>
      ) : null}

      <Disclaimer />

      <button
        type="button"
        className="text-xs text-gray-500 underline mt-3 block disabled:opacity-50"
        disabled={optingOut}
        onClick={() => void handleOptOut()}
      >
        Remove from AI analysis
      </button>
    </div>
  );
}

export default RelationshipIntelPanel;
