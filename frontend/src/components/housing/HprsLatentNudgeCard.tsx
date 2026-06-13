import { useCallback, useEffect, useState } from 'react';
import { X } from 'lucide-react';

interface LatentNudge {
  body: string;
}

interface ReadinessScoreWithLatent {
  latent_nudge?: LatentNudge | null;
}

export interface HprsLatentNudgeCardProps {
  onActivated?: () => void;
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function postHprsAction(path: string): Promise<void> {
  const res = await fetch(path, {
    method: 'POST',
    credentials: 'include',
    headers: buildAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
}

export function HprsLatentNudgeCard({ onActivated }: HprsLatentNudgeCardProps) {
  const [latentNudge, setLatentNudge] = useState<LatentNudge | null>(null);
  const [hidden, setHidden] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetch('/api/housing/readiness-score', {
      credentials: 'include',
      headers: buildAuthHeaders(),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((payload: ReadinessScoreWithLatent | null) => {
        if (cancelled || !payload?.latent_nudge?.body) return;
        setLatentNudge(payload.latent_nudge);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  const hideCard = useCallback(() => {
    setHidden(true);
    setLatentNudge(null);
  }, []);

  const handleSnooze = useCallback(async () => {
    hideCard();
    try {
      await postHprsAction('/api/housing/hprs/snooze-nudge');
    } catch {
      /* silent — card stays hidden for session */
    }
  }, [hideCard]);

  const handleActivate = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    hideCard();
    onActivated?.();
    try {
      await postHprsAction('/api/housing/hprs/activate-from-nudge');
    } catch {
      /* card hidden; readiness card refetch still triggered */
    } finally {
      setBusy(false);
    }
  }, [busy, hideCard, onActivated]);

  if (hidden || !latentNudge) {
    return null;
  }

  return (
    <div className="relative mb-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4">
      <button
        type="button"
        aria-label="Dismiss"
        className="absolute top-3 right-3 text-gray-400 hover:text-gray-300"
        onClick={() => void handleSnooze()}
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex gap-3 pr-6">
        <span className="shrink-0 text-lg" aria-hidden>
          🏠
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-white">{latentNudge.body}</p>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleActivate()}
              className="rounded-full border border-amber-400 px-4 py-2 text-sm text-amber-400 transition hover:bg-amber-400/10 disabled:opacity-50"
            >
              See my readiness score
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleSnooze()}
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300 disabled:opacity-50"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HprsLatentNudgeCard;
