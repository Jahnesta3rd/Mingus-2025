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

type RelationshipStatusAnswer =
  | 'single'
  | 'partnered'
  | 'married'
  | 'separated'
  | 'divorced'
  | 'widowed'
  | 'complicated';

const RELATIONSHIP_STATUS_ROW_1: { label: string; value: RelationshipStatusAnswer }[] = [
  { label: 'Single', value: 'single' },
  { label: 'In a relationship', value: 'partnered' },
  { label: 'Married', value: 'married' },
];

const RELATIONSHIP_STATUS_ROW_2: { label: string; value: RelationshipStatusAnswer }[] = [
  { label: 'Separated', value: 'separated' },
  { label: 'Divorced', value: 'divorced' },
  { label: 'Widowed', value: 'widowed' },
  { label: "It's complicated", value: 'complicated' },
];

const relationshipPillClass = (selected: boolean) =>
  selected
    ? 'rounded-lg border border-purple-600 bg-purple-600 px-4 py-2 text-sm text-white'
    : 'rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:border-purple-500';

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

export default function RosterStep({ onSubmit, onSkip, isSubmitting }: StepProps) {
  const { getAccessToken } = useAuth();
  const [pageError, setPageError] = useState<string | null>(null);
  const [relationshipStatus, setRelationshipStatus] = useState<RelationshipStatusAnswer | null>(
    null
  );
  const [relationshipQuestionSkipped, setRelationshipQuestionSkipped] = useState(false);
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

  const patchRelationshipStatus = useCallback(
    async (status: RelationshipStatusAnswer) => {
      try {
        const res = await fetch('/api/user/me', {
          method: 'PATCH',
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
          body: JSON.stringify({ relationship_status: status }),
        });
        if (!res.ok) {
          console.error('Failed to save relationship_status:', await readErrorMessage(res));
        }
      } catch (err) {
        console.error('Failed to save relationship_status:', err);
      }
    },
    [getAccessToken]
  );

  const finalizeSubmit = useCallback(
    async (peopleOverride?: PeoplePayload[]) => {
      const people = peopleOverride ?? pendingPayload?.people;
      if (!people?.length) return;
      setPhase('submitting');
      setPageError(null);
      try {
        if (relationshipStatus !== null) {
          await patchRelationshipStatus(relationshipStatus);
        }
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
    [fetchRosterCount, onSubmit, patchRelationshipStatus, pendingPayload, relationshipStatus]
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

  const selectRelationshipStatus = (value: RelationshipStatusAnswer) => {
    setRelationshipStatus(value);
    setRelationshipQuestionSkipped(false);
  };

  const skipRelationshipQuestion = () => {
    setRelationshipStatus(null);
    setRelationshipQuestionSkipped(true);
  };

  const renderRelationshipQuestion = () => (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[#1E293B]">Are you currently in a relationship?</h2>
      <p className="mt-1 text-sm text-[#64748B]">Helps us personalize your financial planning.</p>

      {relationshipQuestionSkipped ? (
        <div
          className="mt-4 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3"
          role="status"
          aria-live="polite"
        >
          <p className="text-sm text-[#64748B]">
            Question skipped — you can answer this later from your profile.
          </p>
          <button
            type="button"
            onClick={() => setRelationshipQuestionSkipped(false)}
            className="mt-2 text-sm font-medium text-[#6D28D9] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Answer this question
          </button>
        </div>
      ) : (
        <>
          <div className="mt-4 space-y-3">
            <div className="flex flex-wrap gap-2">
              {RELATIONSHIP_STATUS_ROW_1.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => selectRelationshipStatus(opt.value)}
                  className={relationshipPillClass(relationshipStatus === opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {RELATIONSHIP_STATUS_ROW_2.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => selectRelationshipStatus(opt.value)}
                  className={relationshipPillClass(relationshipStatus === opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <button
            type="button"
            onClick={skipRelationshipQuestion}
            className="mt-3 text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Prefer not to say
          </button>
          <p className="mt-1 text-xs text-[#94A3B8]">
            This only skips the question above. You can still add people below, or skip the whole
            step at the bottom.
          </p>
        </>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {phase === 'seed' ? (
        <>
          {renderRelationshipQuestion()}
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Roster</h1>
            <p className="mt-2 text-sm text-[#64748B]">
              Add people to your roster to personalize relationship and spending insights.
            </p>
          </div>
        </>
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
          isSubmitting={isSubmitting}
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
