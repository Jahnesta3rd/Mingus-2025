import React, { useCallback, useState } from 'react';
import RosterSeedStep, {
  ASSESSABLE_RELATIONSHIP_TYPES,
  type RelationshipType,
} from '../../RosterSeedStep';
import RelationshipCheckPanel from '../RelationshipCheckPanel';
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

type RosterPhase = 'seed' | 'assess' | 'submitting';

type PeoplePayload = {
  nickname: string;
  card_type: 'person' | 'kids' | 'social' | 'family';
  relationship_type: RelationshipType;
  monthly_cost: number;
};

type AssessableEntry = {
  nickname: string;
  serverId: string;
  relationshipType: RelationshipType;
  monthlyCost: number;
};

export default function RosterStep({ onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [pageError, setPageError] = useState<string | null>(null);
  const [phase, setPhase] = useState<RosterPhase>('seed');
  const [assessmentQueue, setAssessmentQueue] = useState<AssessableEntry[]>([]);
  const [queueIndex, setQueueIndex] = useState(0);
  const [pendingPayload, setPendingPayload] = useState<{ people: PeoplePayload[] } | null>(null);

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

  const finalizeSubmit = useCallback(
    async (peopleOverride?: PeoplePayload[]) => {
      const people = peopleOverride ?? pendingPayload?.people;
      if (!people?.length) return;
      setPhase('submitting');
      setPageError(null);
      try {
        const count = await fetchRosterCount();
        await onSubmit({
          count,
          people: people.map((p) => ({
            nickname: p.nickname,
            card_type: p.card_type,
            relationship_type: p.relationship_type,
            monthly_cost: p.monthly_cost,
          })),
        });
      } catch (err) {
        setPhase(peopleOverride ? 'seed' : 'assess');
        setPageError(err instanceof Error ? err.message : 'Could not save roster');
      }
    },
    [fetchRosterCount, onSubmit, pendingPayload]
  );

  const advanceQueue = useCallback(() => {
    const nextIndex = queueIndex + 1;
    if (nextIndex >= assessmentQueue.length) {
      void finalizeSubmit();
    } else {
      setQueueIndex(nextIndex);
    }
  }, [assessmentQueue.length, finalizeSubmit, queueIndex]);

  const handleSeedSubmitted = useCallback(
    (payload: {
      id: string;
      nickname: string;
      people: {
        nickname: string;
        card_type: PeoplePayload['card_type'];
        relationship_type: RelationshipType;
        monthly_cost: number;
        server_id: string;
      }[];
    }) => {
      setPageError(null);
      const people: PeoplePayload[] = payload.people.map((p) => ({
        nickname: p.nickname,
        card_type: p.card_type,
        relationship_type: p.relationship_type,
        monthly_cost: p.monthly_cost,
      }));
      setPendingPayload({ people });

      const queue: AssessableEntry[] = payload.people
        .filter((p) =>
          ASSESSABLE_RELATIONSHIP_TYPES.includes(p.relationship_type as RelationshipType)
        )
        .map((p) => ({
          nickname: p.nickname,
          serverId: p.server_id,
          relationshipType: p.relationship_type,
          monthlyCost: p.monthly_cost,
        }));

      if (queue.length === 0) {
        setAssessmentQueue([]);
        setQueueIndex(0);
        void finalizeSubmit(people);
        return;
      }

      setAssessmentQueue(queue);
      setQueueIndex(0);
      setPhase('assess');
    },
    [finalizeSubmit]
  );

  const currentAssess = assessmentQueue[queueIndex];

  return (
    <div className="space-y-4">
      {phase === 'seed' ? (
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Roster</h1>
          <p className="mt-2 text-sm text-[#64748B]">
            Add people to your roster to personalize relationship and spending insights.
          </p>
        </div>
      ) : null}

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

      {phase === 'seed' ? (
        <RosterSeedStep
          onSubmitted={handleSeedSubmitted}
          onSkip={() => {
            setPageError(null);
            onSkip();
          }}
          setPageError={setPageError}
        />
      ) : null}

      {phase === 'assess' && currentAssess ? (
        <div className="space-y-4">
          <p className="text-sm font-medium text-[#64748B]">
            Partner {queueIndex + 1} of {assessmentQueue.length}: {currentAssess.nickname}
          </p>
          <RelationshipCheckPanel
            key={currentAssess.serverId}
            nickname={currentAssess.nickname}
            personId={currentAssess.serverId}
            onComplete={advanceQueue}
            onSkip={advanceQueue}
          />
        </div>
      ) : null}

      {phase === 'submitting' ? (
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <p className="text-sm text-[#64748B]">Saving your roster…</p>
        </div>
      ) : null}
    </div>
  );
}
