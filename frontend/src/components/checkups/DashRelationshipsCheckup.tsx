import { useCallback, useEffect, useMemo, useState } from 'react';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import ArticleRecommendationStrip from '../ArticleRecommendationStrip';
import { authJsonHeaders, submitRelationshipsCheckup } from './checkupShared';
import { StayOrGoPrompt } from './StayOrGoPrompt';
import { useCheckupFluencyNavigation } from './useCheckupFluencyNavigation';
import {
  CheckupForm,
  CheckupQuestionBlock,
  DollarInput,
  OptionButtons,
  QuestionLabel,
  ScaleButtons,
  SubmitButton,
  TextInput,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';
import {
  deriveUserTier,
  FluencyCue,
} from '../fluency';

type RosterPerson = { id: string; nickname: string; emoji: string | null };

const RELATIONSHIP_QUICK_ADD_OPTIONS = [
  { value: 'partner', label: 'Partner' },
  { value: 'family', label: 'Family' },
  { value: 'friend', label: 'Friend' },
  { value: 'coworker', label: 'Coworker' },
  { value: 'other', label: 'Other' },
] as const;

const FRICTION_OPTIONS = [
  { value: 'financial', label: 'Yes financial' },
  { value: 'emotional', label: 'Yes emotional' },
  { value: 'both', label: 'Yes both' },
  { value: 'no', label: 'No' },
] as const;

const FRICTION_API: Record<string, string> = {
  financial: 'money',
  emotional: 'communication',
  both: 'money',
  no: 'none',
};

const SPENDING_TYPE_OPTIONS = [
  { value: 'planned', label: 'Planned' },
  { value: 'reactive', label: 'Reactive' },
  { value: 'mix', label: 'Mix' },
  { value: 'na', label: 'N/A' },
] as const;

const SPENDING_TYPE_API: Record<string, string> = {
  planned: 'gifts',
  reactive: 'other',
  mix: 'other',
  na: 'other',
};

const DIRECTION_OPTIONS = [
  { value: 'definitely_yes', label: 'Definitely yes' },
  { value: 'mostly_yes', label: 'Mostly yes' },
  { value: 'unsure', label: 'Unsure' },
  { value: 'not_really', label: 'Not really' },
] as const;

const DIRECTION_API: Record<string, string> = {
  definitely_yes: 'improving',
  mostly_yes: 'stable',
  unsure: 'uncertain',
  not_really: 'declining',
};

const AWARENESS_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'somewhat', label: 'Somewhat' },
  { value: 'no', label: 'No' },
] as const;

const AWARENESS_API: Record<string, string> = {
  yes: 'very_aware',
  somewhat: 'somewhat',
  no: 'unaware',
};

const DIRECTION_HISTORY_KEY = (personId: string) => `rel_direction_history_${personId}`;

function readDirectionHistory(personId: string): string[] {
  try {
    const raw = localStorage.getItem(DIRECTION_HISTORY_KEY(personId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

function appendDirectionHistory(personId: string, direction: string): string[] {
  const next = [direction, ...readDirectionHistory(personId)].slice(0, 4);
  try {
    localStorage.setItem(DIRECTION_HISTORY_KEY(personId), JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}

function shouldShowStayOrGo(recentDirections: string[]): boolean {
  const watch = recentDirections.filter((d) => d === 'not_really' || d === 'unsure');
  return watch.length >= 2;
}

function RosterQuickAddForm({
  onAdded,
}: {
  onAdded: (person: RosterPerson) => void;
}) {
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState<string | null>(null);
  const [monthlySpend, setMonthlySpend] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = name.trim().length > 0 && relationship != null;

  const handleAdd = async () => {
    if (!canSave || relationship == null) return;
    setBusy(true);
    setError(null);
    try {
      const spendTrimmed = monthlySpend.trim();
      const spendNum = spendTrimmed !== '' ? Number(spendTrimmed) : null;
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'POST',
        credentials: 'include',
        headers: authJsonHeaders(),
        body: JSON.stringify({
          nickname: name.trim(),
          relationship_type: relationship,
          estimated_monthly_cost: spendNum != null && !Number.isNaN(spendNum) ? spendNum : null,
          card_type: 'person',
        }),
      });
      if (!res.ok) throw new Error('save failed');
      const data = (await res.json()) as { person?: RosterPerson };
      const person = data.person;
      if (!person?.id || !person.nickname) throw new Error('save failed');
      onAdded({
        id: person.id,
        nickname: person.nickname,
        emoji: person.emoji ?? null,
      });
      setName('');
      setRelationship(null);
      setMonthlySpend('');
    } catch {
      setError("Couldn't save — try again");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4 rounded-xl border p-4" style={{ borderColor: 'var(--line)' }}>
      <div>
        <p
          className="text-[14px] font-bold"
          style={{ color: 'var(--ink)', fontFamily: 'Manrope, system-ui, sans-serif' }}
        >
          Add someone to check in on
        </p>
        <p
          className="mt-1 text-[13px]"
          style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
        >
          They&apos;ll be saved to your Roster for future check-ins.
        </p>
      </div>

      <div className="space-y-2">
        <QuestionLabel>Name</QuestionLabel>
        <TextInput
          value={name}
          onChange={setName}
          placeholder="First name or nickname"
        />
      </div>

      <div className="space-y-2">
        <QuestionLabel>Relationship</QuestionLabel>
        <OptionButtons
          options={RELATIONSHIP_QUICK_ADD_OPTIONS}
          value={relationship}
          onChange={setRelationship}
        />
      </div>

      <div className="space-y-2">
        <QuestionLabel>
          Roughly how much do you spend on or with this person per month? (optional)
        </QuestionLabel>
        <DollarInput value={monthlySpend} onChange={setMonthlySpend} />
      </div>

      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => void handleAdd()}
        disabled={busy || !canSave}
        className="dash-checkup-primary min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"
        style={{ background: 'var(--mingus-purple)' }}
      >
        {busy ? 'Saving...' : 'Add to Roster'}
      </button>
    </div>
  );
}

export function DashRelationshipsCheckup() {
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const {
    waterfallContext,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  } = useCheckupFluencyNavigation('relationships', userTier);
  const [roster, setRoster] = useState<RosterPerson[]>([]);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [emotionalScore, setEmotionalScore] = useState(3);
  const [frictionType, setFrictionType] = useState<string | null>(null);
  const [spendingThisWeek, setSpendingThisWeek] = useState<boolean | null>(null);
  const [spendingAmount, setSpendingAmount] = useState('');
  const [spendingType, setSpendingType] = useState<string | null>(null);
  const [direction, setDirection] = useState<string | null>(null);
  const [costAwareness, setCostAwareness] = useState<string | null>(null);
  const [showStayOrGo, setShowStayOrGo] = useState(false);
  const [pendingNavigate, setPendingNavigate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const selectedPerson = roster.find((p) => p.id === selectedPersonId) ?? null;
  const personName = selectedPerson?.nickname ?? 'them';
  const hasRoster = roster.length > 0;

  const handlePersonAdded = useCallback((person: RosterPerson) => {
    setRoster((prev) => [...prev, person]);
    setSelectedPersonId(person.id);
    setShowQuickAdd(false);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      setRosterLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      setRosterLoading(true);
      try {
        const res = await fetch('/api/vibe-tracker/people', {
          credentials: 'include',
          headers: authJsonHeaders(),
        });
        if (!res.ok) throw new Error('roster');
        const data = (await res.json()) as { people?: RosterPerson[] };
        const people = (data.people ?? []).filter((p) => p?.id && p?.nickname);
        if (!cancelled) {
          setRoster(people);
          setShowQuickAdd(people.length === 0);
          if (people.length === 1) setSelectedPersonId(people[0].id);
        }
      } catch {
        if (!cancelled) {
          setRoster([]);
          setShowQuickAdd(true);
        }
      } finally {
        if (!cancelled) setRosterLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const canSubmit = useMemo(() => {
    if (!hasRoster || selectedPersonId == null) return false;
    if (frictionType == null || spendingThisWeek == null || direction == null || costAwareness == null) {
      return false;
    }
    if (spendingThisWeek && spendingType == null) return false;
    return true;
  }, [
    costAwareness,
    direction,
    frictionType,
    hasRoster,
    selectedPersonId,
    spendingThisWeek,
    spendingType,
  ]);

  const finishFlow = useCallback(() => {
    setShowStayOrGo(false);
    setPendingNavigate(true);
    setSuccessMessage('Check-in saved');
    void loadFluencyContext();
  }, [loadFluencyContext]);

  const submit = useCallback(async () => {
    if (!canSubmit || selectedPersonId == null || direction == null) return;
    setBusy(true);
    setError(null);
    try {
      await submitRelationshipsCheckup({
        relationship_friction_type: FRICTION_API[frictionType!] ?? 'none',
        relationship_spending_this_week: spendingThisWeek!,
        relationship_spending_amount: spendingThisWeek
          ? spendingAmount.trim() !== ''
            ? Number(spendingAmount)
            : 0
          : null,
        relationship_spending_type: spendingThisWeek
          ? SPENDING_TYPE_API[spendingType ?? 'na'] ?? 'other'
          : null,
        relationship_direction: DIRECTION_API[direction] ?? 'stable',
        relationship_cost_awareness: AWARENESS_API[costAwareness!] ?? 'somewhat',
        relationship_future_intention: 'maintain',
      });

      const history = appendDirectionHistory(selectedPersonId, direction);
      if (shouldShowStayOrGo(history)) {
        setShowStayOrGo(true);
      } else {
        finishFlow();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    canSubmit,
    costAwareness,
    direction,
    finishFlow,
    frictionType,
    selectedPersonId,
    spendingAmount,
    spendingThisWeek,
    spendingType,
  ]);

  const onSpendingThisWeekChange = (val: boolean) => {
    setSpendingThisWeek(val);
    if (!val) {
      setSpendingAmount('');
      setSpendingType(null);
    }
  };

  const lastAt = profile?.relationship_friction_type != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Relationships Check-in"
      lastCompletedAt={lastAt}
      loading={profileLoading || rosterLoading}
      error={error}
      successMessage={successMessage}
    >
      <StayOrGoPrompt
        open={showStayOrGo}
        personName={personName}
        onDismiss={finishFlow}
      />

      {successMessage ? (
        <ArticleRecommendationStrip
          heading="Free game for you"
          subheading="Based on your check-in"
          className="mt-4"
        />
      ) : null}

      {successMessage && waterfallContext && pendingNavigate ? (
        <FluencyCue
          context={waterfallContext}
          domain="relationships"
          userTier={userTier}
          onActionRoute={onCueActionRoute}
          onDismiss={onCueDismiss}
        />
      ) : null}

      {!successMessage && !showStayOrGo ? (
        <div
          className="dash-checkup-theme max-h-[70vh] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <CheckupForm>
            <CheckupQuestionBlock>
              <QuestionLabel>Who are you checking in on today?</QuestionLabel>

              {showQuickAdd || !hasRoster ? (
                <RosterQuickAddForm onAdded={handlePersonAdded} />
              ) : null}

              {hasRoster ? (
                <>
                  <div className="flex flex-wrap gap-2">
                    {roster.map((person) => {
                      const active = selectedPersonId === person.id;
                      return (
                        <button
                          key={person.id}
                          type="button"
                          onClick={() => setSelectedPersonId(person.id)}
                          className={`rounded-full border px-4 py-2 text-sm transition ${
                            active
                              ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)] font-medium'
                              : ''
                          }`}
                          style={{ borderColor: active ? undefined : 'var(--line)' }}
                          aria-pressed={active}
                        >
                          {person.emoji ? `${person.emoji} ` : ''}
                          {person.nickname}
                        </button>
                      );
                    })}
                  </div>
                  {!showQuickAdd ? (
                    <button
                      type="button"
                      onClick={() => setShowQuickAdd(true)}
                      className="text-left text-[13px] hover:underline"
                      style={{
                        color: 'var(--mingus-purple)',
                        fontFamily: 'Manrope, system-ui, sans-serif',
                      }}
                    >
                      + Add someone new
                    </button>
                  ) : null}
                </>
              ) : null}
            </CheckupQuestionBlock>

            {hasRoster && selectedPersonId ? (
              <>
                <CheckupQuestionBlock conditional>
                  <QuestionLabel>
                    How connected did you feel to {personName} this week?
                  </QuestionLabel>
                  <ScaleButtons
                    min={1}
                    max={5}
                    value={emotionalScore}
                    onChange={setEmotionalScore}
                    labels={{ 1: 'Distant', 3: 'Present', 5: 'Close' }}
                  />
                </CheckupQuestionBlock>

                <CheckupQuestionBlock>
                  <QuestionLabel>
                    Were there any points of friction — financial, emotional, or both — between you
                    and {personName} this week?
                  </QuestionLabel>
                  <OptionButtons
                    options={FRICTION_OPTIONS}
                    value={frictionType}
                    onChange={setFrictionType}
                  />
                </CheckupQuestionBlock>

                <CheckupQuestionBlock>
                  <QuestionLabel>
                    Did you spend money on or because of {personName} this week?
                  </QuestionLabel>
                  <YesNoButtons value={spendingThisWeek} onChange={onSpendingThisWeekChange} />
                </CheckupQuestionBlock>

                {spendingThisWeek === true ? (
                  <>
                    <CheckupQuestionBlock conditional>
                      <QuestionLabel>Roughly how much? (optional)</QuestionLabel>
                      <DollarInput value={spendingAmount} onChange={setSpendingAmount} />
                    </CheckupQuestionBlock>

                    <CheckupQuestionBlock conditional>
                      <QuestionLabel>Was that spending planned or reactive?</QuestionLabel>
                      <OptionButtons
                        options={SPENDING_TYPE_OPTIONS}
                        value={spendingType}
                        onChange={setSpendingType}
                      />
                    </CheckupQuestionBlock>
                  </>
                ) : null}

                <CheckupQuestionBlock>
                  <QuestionLabel>
                    Is this relationship moving in the direction you want?
                  </QuestionLabel>
                  <OptionButtons options={DIRECTION_OPTIONS} value={direction} onChange={setDirection} />
                </CheckupQuestionBlock>

                <CheckupQuestionBlock>
                  <QuestionLabel>
                    Do you feel like {personName} understands or respects your financial situation
                    and goals?
                  </QuestionLabel>
                  <OptionButtons
                    options={AWARENESS_OPTIONS}
                    value={costAwareness}
                    onChange={setCostAwareness}
                  />
                </CheckupQuestionBlock>

                <SubmitButton busy={busy} disabled={!canSubmit} onClick={() => void submit()} />
              </>
            ) : null}
          </CheckupForm>
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashRelationshipsCheckup;
