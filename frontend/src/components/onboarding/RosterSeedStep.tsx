import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

export type RosterCardType = 'person' | 'kids' | 'social' | 'family';

export type RelationshipType =
  | 'talking'
  | 'dating'
  | 'serious'
  | 'engaged'
  | 'married'
  | 'situationship'
  | 'ex';

export const RELATIONSHIP_TYPE_OPTIONS: { value: RelationshipType; label: string }[] = [
  { value: 'talking', label: 'Talking — getting to know' },
  { value: 'dating', label: 'Dating — actively seeing' },
  { value: 'serious', label: 'Serious — committed, exclusive' },
  { value: 'engaged', label: 'Engaged' },
  { value: 'married', label: 'Married' },
  { value: 'situationship', label: 'Situationship — undefined' },
  { value: 'ex', label: 'Ex — still relevant to your life' },
];

export const ASSESSABLE_RELATIONSHIP_TYPES: RelationshipType[] = [
  'serious',
  'engaged',
  'married',
  'situationship',
  'ex',
];

export interface RosterSeedStepProps {
  onSubmitted: (payload: {
    id: string;
    nickname: string;
    people: {
      nickname: string;
      card_type: RosterCardType;
      relationship_type: RelationshipType;
      monthly_cost: number;
      server_id: string;
    }[];
  }) => void;
  onSkip: () => void;
  setPageError: (msg: string | null) => void;
}

interface VibePersonPayload {
  id: string;
  nickname: string;
  card_type: string;
}

interface CreatePersonResponse {
  person: VibePersonPayload;
}

type RosterPersonRow = {
  id: string;
  nickname: string;
  cardType: RosterCardType;
  relationshipType: RelationshipType;
  estimatedMonthlyCost: string;
  serverId?: string;
};

const UI_CAP = 50;

function newRowId(): string {
  return crypto.randomUUID();
}

function authTier(user: { tier?: string; is_beta?: boolean } | null): 'budget' | 'mid_tier' | 'professional' | null {
  if (!user) return null;
  if (user.is_beta === true || user.tier === 'professional') return 'professional';
  if (user.tier === 'mid_tier' || user.tier === 'mid') return 'mid_tier';
  return 'budget';
}

/** Max nickname rows we allow in this form (matches vibe_tracker_service.check_person_limit + UI cap). */
function maxFormRowsForTier(tier: 'budget' | 'mid_tier' | 'professional' | null, existingActiveCount: number): number {
  if (tier === null) return UI_CAP;
  if (tier === 'professional') return UI_CAP;
  if (tier === 'mid_tier') return Math.max(0, 6 - existingActiveCount);
  return Math.max(0, 2 - existingActiveCount);
}

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

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';
const helperClass = 'mt-1 text-xs text-[#64748B]';

const CATEGORY_OPTIONS: { value: RosterCardType; label: string }[] = [
  { value: 'family', label: 'Family' },
  { value: 'person', label: 'Dating / seeing' },
  { value: 'kids', label: 'My child' },
  { value: 'social', label: 'Friend / other' },
];

const DEFAULT_RELATIONSHIP_TYPE: RelationshipType = 'talking';

function emptyRow(): RosterPersonRow {
  return {
    id: newRowId(),
    nickname: '',
    cardType: 'person',
    relationshipType: DEFAULT_RELATIONSHIP_TYPE,
    estimatedMonthlyCost: '',
  };
}

export default function RosterSeedStep({ onSubmitted, onSkip, setPageError }: RosterSeedStepProps) {
  const { getAccessToken, user } = useAuth();
  const [people, setPeople] = useState<RosterPersonRow[]>(() => [emptyRow()]);
  const [existingRosterCount, setExistingRosterCount] = useState(0);
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const tier = authTier(user);
  const maxRows = maxFormRowsForTier(tier, existingRosterCount);
  const tierHasFiniteCap = tier === 'mid_tier' || tier === 'budget';
  const addSlotsRemaining = tierHasFiniteCap ? Math.max(0, maxRows - people.length) : null;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/vibe-tracker/people', {
          method: 'GET',
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
        });
        if (!res.ok) return;
        const json = (await res.json()) as { people?: unknown[] };
        const n = Array.isArray(json.people) ? json.people.length : 0;
        if (!cancelled) setExistingRosterCount(n);
      } catch {
        /* ignore */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  const postPerson = useCallback(
    async (nickname: string, card_type: RosterCardType): Promise<VibePersonPayload> => {
      const name = nickname.trim();
      if (!name) {
        throw new Error('Nickname is required.');
      }
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({ nickname: name, card_type }),
      });
      if (res.status !== 201 && res.status !== 200) {
        throw new Error(await readErrorMessage(res));
      }
      const json = (await res.json()) as CreatePersonResponse;
      return json.person;
    },
    [getAccessToken]
  );

  const updatePerson = useCallback(
    (id: string, patch: Partial<Pick<RosterPersonRow, 'nickname' | 'cardType' | 'relationshipType' | 'estimatedMonthlyCost'>>) => {
      setRowErrors((prev) => {
        if (!prev[id]) return prev;
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setPeople((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)));
    },
    []
  );

  const addRow = useCallback(() => {
    setPageError(null);
    setPeople((prev) => {
      if (prev.length >= maxRows) return prev;
      return [...prev, emptyRow()];
    });
  }, [maxRows, setPageError]);

  const removeRow = useCallback((id: string) => {
    setPageError(null);
    setRowErrors((prev) => {
      if (!prev[id]) return prev;
      const next = { ...prev };
      delete next[id];
      return next;
    });
    setPeople((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((p) => p.id !== id);
    });
  }, [setPageError]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPageError(null);
    setRowErrors({});

    const entries = people
      .map((p) => ({ ...p, nick: p.nickname.trim() }))
      .filter((p) => p.nick.length > 0);

    if (!entries.length) {
      setPageError('Add at least one nickname or skip for now.');
      return;
    }

    for (const row of entries) {
      const cost = parseFloat(row.estimatedMonthlyCost);
      if (row.estimatedMonthlyCost.trim() === '' || Number.isNaN(cost) || cost < 0) {
        setPageError(`Monthly cost is required for ${row.nick}.`);
        return;
      }
    }

    if (entries.length > maxRows) {
      setPageError(
        tier === 'mid_tier'
          ? 'Mid-tier allows up to 6 people on your roster. Remove a row or finish later in Roster.'
          : tier === 'budget'
            ? 'Budget allows up to 2 people on your roster. Remove a row or upgrade for more.'
            : 'You cannot add more people on your current plan.'
      );
      return;
    }

    setSubmitting(true);
    let firstPosted: VibePersonPayload | null = null;
    const postedPeople: {
      nickname: string;
      card_type: RosterCardType;
      relationship_type: RelationshipType;
      monthly_cost: number;
      server_id: string;
    }[] = [];

    try {
      for (const row of entries) {
        try {
          const created = await postPerson(row.nick, row.cardType);
          if (!firstPosted) firstPosted = created;
          const monthlyCost = parseFloat(row.estimatedMonthlyCost);
          postedPeople.push({
            nickname: row.nick,
            card_type: row.cardType,
            relationship_type: row.relationshipType,
            monthly_cost: monthlyCost,
            server_id: created.id,
          });
          setPeople((prev) =>
            prev.map((p) => (p.id === row.id ? { ...p, serverId: created.id } : p))
          );
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Could not add';
          setRowErrors({ [row.id]: msg });
          setPageError(
            firstPosted
              ? `${firstPosted.nickname} was added, but ${row.nick} could not be saved: ${msg}`
              : msg
          );
          return;
        }
      }
      if (firstPosted) {
        onSubmitted({
          id: firstPosted.id,
          nickname: firstPosted.nickname,
          people: postedPeople,
        });
      }
    } catch (err) {
      setPageError(err instanceof Error ? err.message : 'Could not add to roster');
    } finally {
      setSubmitting(false);
    }
  };

  const canAddAnother = people.length < maxRows && maxRows > 0;
  const addAnotherLabel =
    tier === 'mid_tier' && addSlotsRemaining !== null
      ? `Add another (${addSlotsRemaining} remaining)`
      : 'Add another';

  const hasAnyNickname = people.some((p) => p.nickname.trim().length > 0);

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          Who&apos;s on your mind right now?
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add people you want to keep track of — family, friends, dating, kids. Use nicknames; this is just for you.
        </p>

        <div className="mt-6 space-y-6">
          {people.map((row, idx) => (
            <div
              key={row.id}
              className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:p-5"
            >
              <div className="mb-3 flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-[#64748B]">Person {idx + 1}</p>
                {idx > 0 ? (
                  <button
                    type="button"
                    onClick={() => removeRow(row.id)}
                    className="min-h-11 min-w-11 shrink-0 rounded-lg border border-[#E2E8F0] bg-white text-lg leading-none text-[#64748B] transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
                    aria-label={`Remove person ${idx + 1}`}
                  >
                    ×
                  </button>
                ) : null}
              </div>

              <div className="space-y-3">
                <div>
                  <label className={labelClass} htmlFor={`roster-nick-${row.id}`}>
                    Nickname
                  </label>
                  <input
                    id={`roster-nick-${row.id}`}
                    className={inputClass}
                    placeholder="e.g. Lex, Jordan, Mom"
                    value={row.nickname}
                    onChange={(e) => updatePerson(row.id, { nickname: e.target.value })}
                    autoComplete="off"
                  />
                </div>
                <div>
                  <label className={labelClass} htmlFor={`roster-card-${row.id}`}>
                    Category
                  </label>
                  <select
                    id={`roster-card-${row.id}`}
                    className={inputClass}
                    value={row.cardType}
                    onChange={(e) =>
                      updatePerson(row.id, { cardType: e.target.value as RosterCardType })
                    }
                    aria-label={`Category for person ${idx + 1}`}
                  >
                    {CATEGORY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass} htmlFor={`roster-rel-${row.id}`}>
                    Relationship type
                  </label>
                  <select
                    id={`roster-rel-${row.id}`}
                    className={inputClass}
                    value={row.relationshipType}
                    onChange={(e) =>
                      updatePerson(row.id, {
                        relationshipType: e.target.value as RelationshipType,
                      })
                    }
                    aria-label={`Relationship type for person ${idx + 1}`}
                    required
                  >
                    {RELATIONSHIP_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass} htmlFor={`roster-cost-${row.id}`}>
                    Estimated monthly cost ($)
                  </label>
                  <input
                    id={`roster-cost-${row.id}`}
                    type="number"
                    min={0}
                    step={0.01}
                    className={inputClass}
                    value={row.estimatedMonthlyCost}
                    onChange={(e) =>
                      updatePerson(row.id, { estimatedMonthlyCost: e.target.value })
                    }
                    aria-label={`Estimated monthly cost for person ${idx + 1}`}
                    required
                  />
                  <p className={helperClass}>
                    What you typically spend on or with this person each month (gifts, dates, support, etc.).
                  </p>
                </div>
                {rowErrors[row.id] ? (
                  <p className="text-sm text-red-600" role="alert">
                    {rowErrors[row.id]}
                  </p>
                ) : null}
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={addRow}
            disabled={!canAddAnother}
            className="min-h-11 w-full rounded-xl border border-[#E2E8F0] bg-white py-3 text-sm font-semibold text-[#5B2D8E] transition hover:bg-[#F5F3FF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {addAnotherLabel}
          </button>
        </div>
      </div>

      <button
        type="submit"
        disabled={submitting || !hasAnyNickname}
        className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50"
      >
        {submitting ? 'Adding…' : 'Add to my Roster →'}
      </button>

      {/* Skip button removed pending R-A (no-one-to-enter) follow-up. */}
    </form>
  );
}
