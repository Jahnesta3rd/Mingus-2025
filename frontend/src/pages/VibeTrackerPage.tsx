import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import {
  useVibeTracker,
  type TrackedPersonDetail,
  type TrackedPersonListItem,
  type VibeCardType,
} from '../hooks/useVibeTracker';
import { PersonCard } from '../components/vibe-checkups/PersonCard';
import { AssessmentTimeline } from '../components/vibe-checkups/AssessmentTimeline';
import { StayOrGoSignal } from '../components/vibe-checkups/StayOrGoSignal';
import SelfCard from '../components/roster/SelfCard';
import { RosterSection } from '../components/roster/RosterSection';
import ReEntryBanner from '../components/roster/ReEntryBanner';

export default function VibeTrackerPage() {
  const { user } = useAuth();
  const {
    data,
    archivedData,
    loading,
    error,
    getPeople,
    getArchivedPeople,
    getPerson,
    archivePerson,
    unarchivePerson,
    deletePerson,
    createPerson,
  } = useVibeTracker();

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<TrackedPersonDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [archivedOpen, setArchivedOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TrackedPersonListItem | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [addStep, setAddStep] = useState<'type' | 'details'>('type');
  const [addCardType, setAddCardType] = useState<VibeCardType | null>(null);
  const [addNickname, setAddNickname] = useState('');
  const [addEmoji, setAddEmoji] = useState('');
  const [addBusy, setAddBusy] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [reEntryByPersonId, setReEntryByPersonId] = useState<
    Record<
      string,
      {
        nickname: string;
        reEntryType: 'zombie' | 'submarine';
        previousFadeTier: string;
        previousScore: number | null;
        daysSinceLast: number;
      }
    >
  >({});
  const detailRequestSeq = useRef(0);

  const people = data ?? [];
  const archived = archivedData ?? [];
  const activeCount = people.length;

  useEffect(() => {
    void getPeople().catch(() => {});
    void getArchivedPeople().catch(() => {});
  }, [getPeople, getArchivedPeople]);

  const toggleExpand = useCallback(
    async (id: string) => {
      if (expandedId === id) {
        detailRequestSeq.current += 1;
        setExpandedId(null);
        setExpandedDetail(null);
        setDetailLoading(false);
        return;
      }
      setExpandedId(id);
      const seq = ++detailRequestSeq.current;
      setDetailLoading(true);
      setExpandedDetail(null);
      try {
        const d = await getPerson(id, { trackLoading: false });
        if (detailRequestSeq.current === seq) setExpandedDetail(d);
      } catch {
        if (detailRequestSeq.current === seq) setExpandedDetail(null);
      } finally {
        if (detailRequestSeq.current === seq) setDetailLoading(false);
      }
    },
    [expandedId, getPerson]
  );

  useEffect(() => {
    if (expandedId && !people.some((p) => p.id === expandedId) && !archived.some((p) => p.id === expandedId)) {
      setExpandedId(null);
      setExpandedDetail(null);
    }
  }, [people, archived, expandedId]);

  const openAddModal = useCallback(() => {
    setAddError(null);
    setAddStep('type');
    setAddCardType(null);
    setAddNickname('');
    setAddEmoji('');
    setAddOpen(true);
  }, []);

  const closeAddModal = useCallback(() => {
    if (addBusy) return;
    setAddOpen(false);
  }, [addBusy]);

  const dismissReEntryBanner = useCallback((personId: string) => {
    setReEntryByPersonId((prev) => {
      if (!(personId in prev)) return prev;
      const next = { ...prev };
      delete next[personId];
      return next;
    });
  }, []);

  const submitAddPerson = useCallback(async () => {
    const nick = addNickname.trim();
    if (!addCardType || !nick || addBusy) return;
    setAddBusy(true);
    setAddError(null);
    const emoji =
      addCardType === 'kids'
        ? '👶'
        : addEmoji.trim().slice(0, 8) || null;
    try {
      const result = await createPerson(nick, emoji, addCardType);
      if (result.re_entry_detected && result.re_entry_type) {
        setReEntryByPersonId((prev) => ({
          ...prev,
          [result.person.id]: {
            nickname: result.person.nickname,
            reEntryType: result.re_entry_type,
            previousFadeTier: result.previous_fade_tier ?? '',
            previousScore: result.previous_score,
            daysSinceLast: result.days_since_last ?? 0,
          },
        }));
      }
      setAddOpen(false);
      await getPeople().catch(() => {});
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Could not add');
    } finally {
      setAddBusy(false);
    }
  }, [addBusy, addCardType, addEmoji, addNickname, createPerson, getPeople]);

  const runDelete = useCallback(async () => {
    if (!deleteTarget || deleteConfirm !== 'REMOVE' || deleteBusy) return;
    const id = deleteTarget.id;
    setDeleteBusy(true);
    try {
      await deletePerson(id);
      setDeleteTarget(null);
      setDeleteConfirm('');
      setReEntryByPersonId((prev) => {
        if (!(id in prev)) return prev;
        const next = { ...prev };
        delete next[id];
        return next;
      });
      if (expandedId === id) {
        setExpandedId(null);
        setExpandedDetail(null);
      }
    } finally {
      setDeleteBusy(false);
    }
  }, [deleteBusy, deleteConfirm, deletePerson, deleteTarget, expandedId]);

  const showMidLimitBanner = user?.tier === 'mid_tier' && activeCount >= 3;

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#0d0a08] px-4 py-8 text-[#F0E8D8] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 text-center sm:text-left">
          <h1 className="font-display text-2xl font-semibold text-[#F0E8D8] sm:text-3xl">Your Roster</h1>
          <p className="mt-1 text-sm text-[#9a8f7e]">How you show up — and who you show up for.</p>
        </header>

        {showMidLimitBanner ? (
          <div className="mb-8 rounded-2xl border border-[#A78BFA]/35 bg-[#A78BFA]/10 px-5 py-4 text-sm leading-relaxed text-[#F0E8D8]">
            <p className="font-medium text-[#A78BFA]">You&apos;ve reached the 3-person limit on Mid-tier.</p>
            <p className="mt-1 text-[#9a8f7e]">Upgrade to Professional for unlimited tracking.</p>
            <Link
              to="/settings/upgrade"
              className="mt-3 inline-block text-sm font-semibold text-[#A78BFA] underline-offset-2 hover:underline"
            >
              Upgrade
            </Link>
          </div>
        ) : null}

        <RosterSection title="Your inner life" titleClassName="text-[#A78BFA]/90">
          <SelfCard />
        </RosterSection>

        <div className="mt-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="h-px min-w-0 flex-1 bg-[#2a2030]" aria-hidden />
            <span className="shrink-0 text-center text-[10px] leading-none text-[#9a8f7e]">— relationship to others —</span>
            <div className="h-px min-w-0 flex-1 bg-[#2a2030]" aria-hidden />
          </div>
        </div>

        <RosterSection
          title="Your outer circle"
          subtitle={`${activeCount} ${activeCount === 1 ? 'person' : 'people'} tracked`}
        >
          <div className="mb-4 flex justify-end">
            <button
              type="button"
              onClick={openAddModal}
              disabled={showMidLimitBanner}
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#A78BFA]/50 bg-transparent px-4 text-sm font-semibold text-[#A78BFA] transition hover:border-[#A78BFA] hover:bg-[#A78BFA]/10 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Add someone
            </button>
          </div>
          {error && !loading ? (
            <p className="mb-6 rounded-xl border border-rose-900/50 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">{error}</p>
          ) : null}

          {loading && people.length === 0 && archived.length === 0 ? (
            <p className="text-center text-sm text-[#9a8f7e]">Loading…</p>
          ) : null}

          {!loading && people.length === 0 ? (
            <div className="mx-auto max-w-md rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 px-8 py-12 text-center shadow-lg">
              <div
                className="mx-auto mb-6 flex h-28 w-28 items-center justify-center rounded-2xl border border-dashed border-[#2a2030] bg-[#0d0a08] text-5xl opacity-90"
                aria-hidden
              >
                💞
              </div>
              <p className="text-sm leading-relaxed text-[#F0E8D8]/90">
                Start tracking someone — take a checkup and give them a nickname.
              </p>
              <Link
                to="/dashboard/vibe-checkups"
                className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-[#5B2D8E] py-3.5 text-sm font-semibold text-white transition hover:opacity-95 sm:w-auto sm:px-8"
              >
                Take a Checkup
              </Link>
            </div>
          ) : null}

          {people.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {people.map((row) => (
                <div key={row.id} className={expandedId === row.id ? 'md:col-span-2' : undefined}>
                  {reEntryByPersonId[row.id] ? (
                    <ReEntryBanner
                      nickname={reEntryByPersonId[row.id].nickname}
                      reEntryType={reEntryByPersonId[row.id].reEntryType}
                      previousFadeTier={reEntryByPersonId[row.id].previousFadeTier}
                      previousScore={reEntryByPersonId[row.id].previousScore}
                      daysSinceLast={reEntryByPersonId[row.id].daysSinceLast}
                      onDismiss={() => dismissReEntryBanner(row.id)}
                    />
                  ) : null}
                  <PersonCard
                    person={row}
                    trend={row.trend}
                    latestAssessment={row.latest_assessment}
                    onClick={() => void toggleExpand(row.id)}
                    isExpanded={expandedId === row.id}
                    onArchive={() => void archivePerson(row.id)}
                    onDelete={() => setDeleteTarget(row)}
                  />
                  {expandedId === row.id ? (
                    <div className="mt-4 rounded-2xl border border-[#2a2030] bg-[#1a1520]/60 p-4 sm:p-6">
                      {detailLoading ? (
                        <p className="text-center text-sm text-[#9a8f7e]">Loading history…</p>
                      ) : expandedDetail && expandedDetail.id === row.id ? (
                        <>
                          <AssessmentTimeline assessments={expandedDetail.assessments} />
                          {expandedDetail.trend ? <StayOrGoSignal trend={expandedDetail.trend} /> : null}
                          <div className="mt-6 text-center">
                            <Link
                              to="/dashboard/vibe-checkups"
                              className="inline-flex rounded-xl border border-[#A78BFA]/60 bg-transparent px-6 py-3 text-sm font-semibold text-[#A78BFA] transition hover:border-[#A78BFA] hover:bg-[#A78BFA]/10"
                            >
                              Re-assess this person
                            </Link>
                          </div>
                        </>
                      ) : (
                        <p className="text-center text-sm text-[#9a8f7e]">Could not load checkup history.</p>
                      )}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}

          {archivedData !== null ? (
            <div className="mt-12 border-t border-[#2a2030] pt-8">
              <button
                type="button"
                onClick={() => setArchivedOpen((o) => !o)}
                className="flex w-full items-center justify-between rounded-xl border border-[#2a2030] bg-[#1a1520]/50 px-4 py-3 text-left text-sm font-medium text-[#F0E8D8] transition hover:border-[#A78BFA]/30"
              >
                <span>Archived ({archived.length})</span>
                {archivedOpen ? (
                  <ChevronDownIcon className="h-5 w-5 text-[#9a8f7e]" />
                ) : (
                  <ChevronRightIcon className="h-5 w-5 text-[#9a8f7e]" />
                )}
              </button>
              {archivedOpen ? (
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  {archived.length === 0 ? (
                    <p className="text-sm text-[#9a8f7e]">No archived people.</p>
                  ) : (
                    archived.map((row) => (
                      <div key={row.id}>
                        <PersonCard
                          person={row}
                          trend={row.trend}
                          latestAssessment={row.latest_assessment}
                          onClick={() => void toggleExpand(row.id)}
                          isExpanded={expandedId === row.id}
                          isArchived
                          onRestore={() => void unarchivePerson(row.id)}
                          onDelete={() => setDeleteTarget(row)}
                        />
                        {expandedId === row.id ? (
                          <div className="mt-4 rounded-2xl border border-[#2a2030] bg-[#1a1520]/60 p-4 sm:p-6">
                            {detailLoading ? (
                              <p className="text-center text-sm text-[#9a8f7e]">Loading history…</p>
                            ) : expandedDetail && expandedDetail.id === row.id ? (
                              <>
                                <AssessmentTimeline assessments={expandedDetail.assessments} />
                                {expandedDetail.trend ? <StayOrGoSignal trend={expandedDetail.trend} /> : null}
                                <div className="mt-6 text-center">
                                  <Link
                                    to="/dashboard/vibe-checkups"
                                    className="inline-flex rounded-xl border border-[#A78BFA]/60 bg-transparent px-6 py-3 text-sm font-semibold text-[#A78BFA] transition hover:border-[#A78BFA] hover:bg-[#A78BFA]/10"
                                  >
                                    Re-assess this person
                                  </Link>
                                </div>
                              </>
                            ) : (
                              <p className="text-center text-sm text-[#9a8f7e]">Could not load checkup history.</p>
                            )}
                          </div>
                        ) : null}
                      </div>
                    ))
                  )}
                </div>
              ) : null}
            </div>
          ) : null}
        </RosterSection>
      </div>

      {addOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="roster-add-title"
        >
          <div className="w-full max-w-md rounded-2xl border border-[#2a2030] bg-[#1a1520] p-6 shadow-2xl">
            <h2 id="roster-add-title" className="font-display text-lg font-semibold text-[#F0E8D8]">
              {addStep === 'type' ? 'Who are you adding?' : 'Name this entry'}
            </h2>

            {addStep === 'type' ? (
              <div className="mt-6 space-y-3">
                <button
                  type="button"
                  onClick={() => {
                    setAddCardType('person');
                    setAddStep('details');
                  }}
                  className="flex w-full min-h-11 items-center gap-3 rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-left text-sm text-[#F0E8D8] transition hover:border-[#A78BFA]/40"
                >
                  <span className="text-2xl" aria-hidden>
                    👤
                  </span>
                  <span>A person I&apos;m dating or seeing</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAddCardType('kids');
                    setAddStep('details');
                  }}
                  className="flex w-full min-h-11 items-center gap-3 rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-left text-sm text-[#F0E8D8] transition hover:border-[#059669]/45"
                >
                  <span className="text-2xl" aria-hidden>
                    👶
                  </span>
                  <span>My child / children</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAddCardType('social');
                    setAddStep('details');
                  }}
                  className="flex w-full min-h-11 items-center gap-3 rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-left text-sm text-[#F0E8D8] transition hover:border-[#A78BFA]/40"
                >
                  <span className="text-2xl" aria-hidden>
                    👥
                  </span>
                  <span>A friend or social connection</span>
                </button>
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {addCardType === 'person' || addCardType === 'social' ? (
                  <div>
                    <label
                      className="block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]"
                      htmlFor="roster-add-emoji"
                    >
                      Emoji (optional)
                    </label>
                    <input
                      id="roster-add-emoji"
                      type="text"
                      value={addEmoji}
                      onChange={(e) => setAddEmoji(e.target.value.slice(0, 8))}
                      maxLength={8}
                      className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-[#F0E8D8] outline-none ring-[#A78BFA]/30 focus:ring-2"
                      placeholder="e.g. ✨"
                    />
                  </div>
                ) : null}
                <div>
                  <label
                    className="block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]"
                    htmlFor="roster-add-nick"
                  >
                    Nickname
                  </label>
                  <input
                    id="roster-add-nick"
                    type="text"
                    value={addNickname}
                    onChange={(e) => setAddNickname(e.target.value.slice(0, 30))}
                    maxLength={30}
                    className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-[#F0E8D8] outline-none ring-[#A78BFA]/30 focus:ring-2"
                    placeholder={
                      addCardType === 'kids' ? 'e.g. The kids, Leo…' : 'e.g. Alex, Best friend…'
                    }
                  />
                </div>
                {addError ? <p className="text-sm text-rose-300">{addError}</p> : null}
                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
                  <button
                    type="button"
                    onClick={() => {
                      setAddStep('type');
                      setAddError(null);
                    }}
                    className="min-h-11 rounded-xl border border-[#2a2030] px-5 py-2.5 text-sm font-medium text-[#F0E8D8] hover:bg-[#0d0a08]"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    disabled={addBusy || !addNickname.trim()}
                    onClick={() => void submitAddPerson()}
                    className="min-h-11 rounded-xl bg-[#5B2D8E] px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:opacity-40"
                  >
                    {addBusy ? 'Saving…' : 'Add to roster'}
                  </button>
                </div>
              </div>
            )}

            {addStep === 'type' ? (
              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={closeAddModal}
                  className="min-h-11 rounded-xl border border-[#2a2030] px-5 py-2.5 text-sm font-medium text-[#F0E8D8] hover:bg-[#0d0a08]"
                >
                  Cancel
                </button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-2xl border border-[#2a2030] bg-[#1a1520] p-6 shadow-2xl">
            <h2 className="font-display text-lg font-semibold text-[#F0E8D8]">
              Remove {deleteTarget.nickname}&apos;s checkup history?
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-[#9a8f7e]">
              This removes all {deleteTarget.assessment_count} checkup{deleteTarget.assessment_count === 1 ? '' : 's'} for{' '}
              {deleteTarget.nickname}. This cannot be undone.
            </p>
            <label className="mt-4 block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]" htmlFor="vc-delete-confirm">
              Type REMOVE to confirm
            </label>
            <input
              id="vc-delete-confirm"
              type="text"
              autoComplete="off"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-[#F0E8D8] outline-none ring-[#A78BFA]/30 focus:ring-2"
              placeholder="REMOVE"
            />
            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => {
                  setDeleteTarget(null);
                  setDeleteConfirm('');
                }}
                className="rounded-xl border border-[#2a2030] px-5 py-2.5 text-sm font-medium text-[#F0E8D8] hover:bg-[#0d0a08]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleteConfirm !== 'REMOVE' || deleteBusy}
                onClick={() => void runDelete()}
                className="rounded-xl bg-rose-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-rose-600 disabled:opacity-40"
              >
                {deleteBusy ? 'Removing…' : 'Yes, Remove History'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
