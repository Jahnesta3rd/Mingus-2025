import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import { useVibeTracker, type TrackedPersonDetail, type TrackedPersonListItem } from '../hooks/useVibeTracker';
import { PersonCard } from '../components/vibe-checkups/PersonCard';
import { AssessmentTimeline } from '../components/vibe-checkups/AssessmentTimeline';
import { StayOrGoSignal } from '../components/vibe-checkups/StayOrGoSignal';
import SelfCard from '../components/roster/SelfCard';
import { RosterSection } from '../components/roster/RosterSection';

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
  } = useVibeTracker();

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<TrackedPersonDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [archivedOpen, setArchivedOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TrackedPersonListItem | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [deleteBusy, setDeleteBusy] = useState(false);
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

  const runDelete = useCallback(async () => {
    if (!deleteTarget || deleteConfirm !== 'REMOVE' || deleteBusy) return;
    const id = deleteTarget.id;
    setDeleteBusy(true);
    try {
      await deletePerson(id);
      setDeleteTarget(null);
      setDeleteConfirm('');
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
          <div className="mb-8 rounded-2xl border border-[#C4A064]/35 bg-[#C4A064]/10 px-5 py-4 text-sm leading-relaxed text-[#F0E8D8]">
            <p className="font-medium text-[#C4A064]">You&apos;ve reached the 3-person limit on Mid-tier.</p>
            <p className="mt-1 text-[#9a8f7e]">Upgrade to Professional for unlimited tracking.</p>
            <Link
              to="/settings/upgrade"
              className="mt-3 inline-block text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
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
                className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074] sm:w-auto sm:px-8"
              >
                Take a Checkup
              </Link>
            </div>
          ) : null}

          {people.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {people.map((row) => (
                <div key={row.id} className={expandedId === row.id ? 'md:col-span-2' : undefined}>
                  <PersonCard
                    person={row}
                    trend={row.trend}
                    latestAssessment={row.latest_assessment}
                    onClick={() => void toggleExpand(row.id)}
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
                              className="inline-flex rounded-xl border border-[#C4A064]/60 bg-transparent px-6 py-3 text-sm font-semibold text-[#C4A064] transition hover:border-[#C4A064] hover:bg-[#C4A064]/10"
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
                className="flex w-full items-center justify-between rounded-xl border border-[#2a2030] bg-[#1a1520]/50 px-4 py-3 text-left text-sm font-medium text-[#F0E8D8] transition hover:border-[#C4A064]/30"
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
                                    className="inline-flex rounded-xl border border-[#C4A064]/60 bg-transparent px-6 py-3 text-sm font-semibold text-[#C4A064] transition hover:border-[#C4A064] hover:bg-[#C4A064]/10"
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
              className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#0d0a08] px-4 py-3 text-[#F0E8D8] outline-none ring-[#C4A064]/30 focus:ring-2"
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
