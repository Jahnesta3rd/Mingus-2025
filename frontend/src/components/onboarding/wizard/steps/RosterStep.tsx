import React, { useCallback, useState } from 'react';
import RosterSeedStep from '../../RosterSeedStep';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { error?: string; message?: string };
    return j.error || j.message || text || res.statusText;
  } catch {
    return text || res.statusText || 'Request failed';
  }
}

export default function RosterStep({ onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [pageError, setPageError] = useState<string | null>(null);

  const fetchRosterCount = useCallback(async (): Promise<number> => {
    const res = await fetch('/api/vibe-tracker/people', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    if (!res.ok) throw new Error(await readErrorMessage(res));
    const json = (await res.json()) as { people?: unknown[] };
    return Array.isArray(json.people) ? json.people.length : 0;
  }, [getAccessToken]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Roster</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add people to your roster to personalize relationship and spending insights.
        </p>
      </div>

      {pageError && (
        <div className="relative rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white" role="alert">
          <button
            type="button"
            className="absolute right-2 top-2 rounded p-1 text-white hover:bg-red-700"
            aria-label="Dismiss error"
            onClick={() => setPageError(null)}
          >
            ×
          </button>
          <span className="pr-8">{pageError}</span>
        </div>
      )}

      <RosterSeedStep
        onSubmitted={async () => {
          setPageError(null);
          const count = await fetchRosterCount();
          await onSubmit({ count });
        }}
        onSkip={() => {
          setPageError(null);
          onSkip();
        }}
        setPageError={setPageError}
      />
    </div>
  );
}
