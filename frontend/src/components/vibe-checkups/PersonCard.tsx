import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  EllipsisVerticalIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusSmallIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import type {
  VibeCardType,
  VibePersonAssessment,
  VibePersonTrend,
  VibeTrackedPerson,
} from '../../hooks/useVibeTracker';
import EventRail from '../roster/EventRail';
import ConnectionTrendBadge from '../roster/ConnectionTrendBadge';
import ConnectionTrendAssessmentModal from '../roster/ConnectionTrendAssessmentModal';

function formatConnectionDaysAgo(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const now = Date.now();
  const dayMs = 86400000;
  const diff = Math.floor((now - d.getTime()) / dayMs);
  if (diff <= 0) return 'today';
  if (diff === 1) return '1 day ago';
  return `${diff} days ago`;
}

function formatRelativePast(iso: string | null): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const now = Date.now();
  const sec = Math.floor((now - then) / 1000);
  if (sec < 45) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} minute${min === 1 ? '' : 's'} ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} hour${hr === 1 ? '' : 's'} ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day} day${day === 1 ? '' : 's'} ago`;
  const week = Math.floor(day / 7);
  if (week < 8) return `${week} week${week === 1 ? '' : 's'} ago`;
  const month = Math.floor(day / 30);
  if (month < 18) return `${month} month${month === 1 ? '' : 's'} ago`;
  const year = Math.floor(day / 365);
  return `${year} year${year === 1 ? '' : 's'} ago`;
}

function TrendGlyph({ trend }: { trend: VibePersonTrend | null }) {
  const dir = trend?.trend_direction ?? 'insufficient_data';
  if (dir === 'insufficient_data') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[#9a8f7e]" title="Too early for a trend">
        <ClockIcon className="h-4 w-4" aria-hidden />
        <span>Too early</span>
      </span>
    );
  }
  if (dir === 'improving') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-400" title="Improving">
        <ArrowTrendingUpIcon className="h-4 w-4" aria-hidden />
        <span>Up</span>
      </span>
    );
  }
  if (dir === 'declining') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-rose-400" title="Declining">
        <ArrowTrendingDownIcon className="h-4 w-4" aria-hidden />
        <span>Down</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-[#9a8f7e]" title="Stable">
      <MinusSmallIcon className="h-4 w-4" aria-hidden />
      <span>Stable</span>
    </span>
  );
}

function MiniBar({ value, label }: { value: number; label: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] uppercase tracking-wide text-[#9a8f7e]">
        <span>{label}</span>
        <span className="tabular-nums text-[#F0E8D8]">{pct}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#2a2030]">
        <div
          className="h-full rounded-full bg-[#A78BFA]"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export type PersonCardProps = {
  person: VibeTrackedPerson;
  trend: VibePersonTrend | null;
  latestAssessment: VibePersonAssessment | null;
  onClick: () => void;
  isExpanded?: boolean;
  isArchived?: boolean;
  onArchive?: () => void;
  onDelete?: () => void;
  onRestore?: () => void;
};

interface PersonEventsApiResponse {
  events: unknown[];
  thirty_day_cost_total: number;
}

interface ParentingCostsApiResponse {
  childcare: number;
  healthcare: number;
  education: number;
  activities: number;
  total_monthly: number;
  coverage_status: 'covered' | 'tight' | 'shortfall' | null;
  balance_after_parenting: number | null;
}

interface ConnectionTrendPatternInsight {
  insight_message: string | null;
  financial_note: string | null;
}

interface ConnectionTrendLatestAssessment {
  id: string;
  assessed_at: string | null;
  fade_tier: string;
  pattern_type: string | null;
  pattern_insight: ConnectionTrendPatternInsight | null;
}

interface ConnectionTrendLatestResponse {
  assessment: ConnectionTrendLatestAssessment | null;
}

type ConnectionTrendFetchStatus = 'loading' | 'ok' | 'empty' | 'hidden';

function formatUsdWhole(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function KidsParentingCosts() {
  const [data, setData] = useState<ParentingCostsApiResponse | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const token = localStorage.getItem('mingus_token') ?? '';
    fetch('/api/wellness/parenting-costs', {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('parenting-costs');
        return res.json() as Promise<ParentingCostsApiResponse>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setVisible(true);
        }
      })
      .catch(() => {
        if (!cancelled) setVisible(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!visible) {
    return (
      <div className="mt-4 space-y-2" aria-hidden>
        <div className="h-4 w-[75%] max-w-full animate-pulse rounded bg-[#2a2030]" />
        <div className="h-4 w-1/2 max-w-full animate-pulse rounded bg-[#2a2030]" />
        <div className="h-4 w-[66%] max-w-full animate-pulse rounded bg-[#2a2030]" />
      </div>
    );
  }

  if (!data) return null;

  const lines: { label: string; amount: number }[] = [
    { label: 'Childcare', amount: data.childcare },
    { label: 'Healthcare', amount: data.healthcare },
    { label: 'Education', amount: data.education },
    { label: 'Activities', amount: data.activities },
  ];

  const coverageLabel = (() => {
    if (!data.coverage_status) return null;
    if (data.coverage_status === 'covered') return 'Covered in forecast';
    if (data.coverage_status === 'tight') return 'Tight in forecast';
    return 'Shortfall risk in forecast';
  })();

  const coverageClass =
    data.coverage_status === 'covered'
      ? 'text-[#059669]'
      : data.coverage_status === 'tight'
        ? 'text-[#D97706]'
        : 'text-[#DC2626]';

  return (
    <div className="mt-4 space-y-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-[#9a8f7e]">
        Monthly parenting costs
      </p>
      <ul className="space-y-2">
        {lines.map((row) => (
          <li key={row.label} className="flex justify-between gap-2 text-sm text-[#F0E8D8]">
            <span className="text-[#9a8f7e]">{row.label}</span>
            <span className="tabular-nums font-medium text-[#F0E8D8]">
              {formatUsdWhole(row.amount)}
            </span>
          </li>
        ))}
      </ul>
      <div className="border-t border-[#2a2030] pt-3">
        <div className="flex justify-between gap-2 text-sm font-semibold text-[#F0E8D8]">
          <span>Total / month</span>
          <span className="tabular-nums text-[#059669]">{formatUsdWhole(data.total_monthly)}</span>
        </div>
        {coverageLabel ? (
          <p className={`mt-2 text-xs font-medium ${coverageClass}`}>{coverageLabel}</p>
        ) : data.total_monthly <= 0 ? (
          <p className="mt-2 text-xs text-[#9a8f7e]">
            Set parenting cost categories in your profile (Health &amp; Wellness) to see coverage.
          </p>
        ) : null}
      </div>
    </div>
  );
}

function CollapsedThirtyDayCost({ personId }: { personId: string }) {
  const [total, setTotal] = useState<number | null>(null);
  const [linkedCount, setLinkedCount] = useState<number | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const token = localStorage.getItem('mingus_token') ?? '';
    fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}/events`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('events');
        return res.json() as Promise<PersonEventsApiResponse>;
      })
      .then((json) => {
        if (!cancelled) {
          const evs = Array.isArray(json.events) ? json.events : [];
          const t =
            typeof json.thirty_day_cost_total === 'number' ? json.thirty_day_cost_total : 0;
          setLinkedCount(evs.length);
          setTotal(t);
          setVisible(true);
        }
      })
      .catch(() => {
        if (!cancelled) setVisible(false);
      });
    return () => {
      cancelled = true;
    };
  }, [personId]);

  if (!visible || total === null || linkedCount === null) return null;

  const label =
    linkedCount === 0
      ? 'No costs linked'
      : `30d: ${new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(total)}`;

  return <p className="mt-1.5 text-xs text-[#9a8f7e]">{label}</p>;
}

export function PersonCard({
  person,
  trend,
  latestAssessment,
  onClick,
  isExpanded = false,
  isArchived = false,
  onArchive,
  onDelete,
  onRestore,
}: PersonCardProps) {
  const cardType: VibeCardType =
    person.card_type === 'kids' || person.card_type === 'social' ? person.card_type : 'person';
  const isKids = cardType === 'kids';

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const [connectionTrendStatus, setConnectionTrendStatus] =
    useState<ConnectionTrendFetchStatus>('loading');
  const [connectionTrendLatest, setConnectionTrendLatest] =
    useState<ConnectionTrendLatestAssessment | null>(null);
  const [observationModalOpen, setObservationModalOpen] = useState(false);

  const loadConnectionTrendLatest = useCallback(() => {
    if (isKids || isArchived) {
      setConnectionTrendStatus('hidden');
      setConnectionTrendLatest(null);
      return;
    }
    setConnectionTrendStatus('loading');
    const token = localStorage.getItem('mingus_token') ?? '';
    fetch(`/api/connection-trend/people/${encodeURIComponent(person.id)}/latest`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('connection-trend');
        return res.json() as Promise<ConnectionTrendLatestResponse>;
      })
      .then((json) => {
        if (json.assessment) {
          setConnectionTrendLatest(json.assessment);
          setConnectionTrendStatus('ok');
        } else {
          setConnectionTrendLatest(null);
          setConnectionTrendStatus('empty');
        }
      })
      .catch(() => {
        setConnectionTrendLatest(null);
        setConnectionTrendStatus('hidden');
      });
  }, [person.id, isKids, isArchived]);

  useEffect(() => {
    loadConnectionTrendLatest();
  }, [loadConnectionTrendLatest]);

  useEffect(() => {
    if (!menuOpen) return;
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [menuOpen]);

  const emo = latestAssessment?.emotional_score ?? 0;
  const fin = latestAssessment?.financial_score ?? 0;
  const hasScores = Boolean(latestAssessment);

  const cardBorderClass = isKids
    ? 'border-[#059669]/35 hover:border-[#059669]/55 focus-visible:ring-[#059669]/35'
    : 'border-[#2a2030] hover:border-[#A78BFA]/35 focus-visible:ring-[#A78BFA]/30';

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      className={`relative cursor-pointer rounded-2xl border bg-[#1a1520]/90 p-4 text-left shadow-lg outline-none ring-offset-0 transition focus-visible:ring-2 ${cardBorderClass}`}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#0d0a08] text-2xl"
          aria-hidden
        >
          {isKids ? '👶' : person.emoji || '·'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-display text-base font-semibold text-[#F0E8D8]">{person.nickname}</h3>
            <span
              className={`shrink-0 rounded-full border border-[#2a2030] bg-[#0d0a08] px-2 py-0.5 text-[10px] font-medium tabular-nums ${
                isKids ? 'text-[#059669]' : 'text-[#A78BFA]'
              }`}
            >
              {person.assessment_count} checkup{person.assessment_count === 1 ? '' : 's'}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xl leading-none" aria-hidden>
              {latestAssessment?.verdict_emoji ?? '…'}
            </span>
            <span className="text-sm text-[#F0E8D8]/90">
              {latestAssessment?.verdict_label ?? 'No checkups yet'}
            </span>
          </div>
          {!isExpanded && !isKids ? <CollapsedThirtyDayCost personId={person.id} /> : null}
        </div>
      </div>

      {isKids ? (
        <div className="mt-1" onClick={(e) => e.stopPropagation()}>
          <KidsParentingCosts />
        </div>
      ) : hasScores ? (
        <div className="mt-4 space-y-2" onClick={(e) => e.stopPropagation()}>
          <MiniBar value={emo} label="Emotional" />
          <MiniBar value={fin} label="Financial" />
        </div>
      ) : (
        <p className="mt-3 text-xs text-[#9a8f7e]">Complete a checkup to see scores here.</p>
      )}

      {!isKids && !isArchived && connectionTrendStatus !== 'hidden' ? (
        <div className="mt-3 space-y-1.5" onClick={(e) => e.stopPropagation()}>
          {connectionTrendStatus === 'loading' ? (
            <div className="space-y-2" aria-hidden>
              <div className="h-8 w-40 max-w-full animate-pulse rounded-lg bg-[#2a2030]" />
              <div className="h-3 w-28 max-w-full animate-pulse rounded bg-[#2a2030]" />
            </div>
          ) : null}
          {connectionTrendStatus === 'ok' && connectionTrendLatest ? (
            <>
              <ConnectionTrendBadge
                fadeTier={connectionTrendLatest.fade_tier}
                patternType={connectionTrendLatest.pattern_type}
                insightMessage={
                  connectionTrendLatest.pattern_insight?.insight_message ?? null
                }
              />
              <p className="text-[10px] text-[#9a8f7e]">
                Last assessed: {formatConnectionDaysAgo(connectionTrendLatest.assessed_at)}
              </p>
            </>
          ) : null}
          {connectionTrendStatus === 'empty' ? (
            <p className="text-[10px] text-[#9a8f7e]">
              Not yet assessed.{' '}
              <button
                type="button"
                className="min-h-11 min-w-0 font-semibold text-[#A78BFA] underline sm:min-h-0"
                onClick={() => setObservationModalOpen(true)}
              >
                Take Observation →
              </button>
            </p>
          ) : null}
        </div>
      ) : null}

      {isExpanded ? <EventRail personId={person.id} nickname={person.nickname} /> : null}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#2a2030]/80 pt-3">
        <div className="flex flex-wrap items-center gap-3">
          <TrendGlyph trend={trend} />
          {!isKids && !isArchived ? (
            <button
              type="button"
              className="min-h-11 text-xs font-semibold text-[#A78BFA] underline sm:min-h-0"
              onClick={(e) => {
                e.stopPropagation();
                setObservationModalOpen(true);
              }}
            >
              Take Observation →
            </button>
          ) : null}
        </div>
        <span className="text-xs text-[#9a8f7e]">Last assessed: {formatRelativePast(person.last_assessed_at)}</span>
      </div>

      <div className="mt-4 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
        {isArchived ? (
          <button
            type="button"
            onClick={() => onRestore?.()}
            className="flex-1 min-h-11 rounded-xl border border-[#A78BFA] bg-transparent px-3 py-2.5 text-sm font-semibold text-[#A78BFA] transition hover:bg-[#A78BFA]/10"
          >
            Restore
          </button>
        ) : isKids ? (
          <Link
            to="/dashboard/profile"
            className="flex-1 min-h-11 rounded-xl border border-[#059669]/60 bg-transparent px-3 py-2.5 text-center text-sm font-semibold text-[#059669] transition hover:border-[#059669] hover:bg-[#059669]/10"
          >
            Update costs →
          </Link>
        ) : (
          <Link
            to="/dashboard/vibe-checkups"
            className="flex-1 min-h-11 rounded-xl border border-[#A78BFA]/60 bg-transparent px-3 py-2.5 text-center text-sm font-semibold text-[#A78BFA] transition hover:border-[#A78BFA] hover:bg-[#A78BFA]/10"
          >
            Re-assess
          </Link>
        )}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            aria-label="More actions"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((o) => !o);
            }}
            className="rounded-lg border border-[#2a2030] p-2 text-[#F0E8D8] transition hover:border-[#A78BFA]/40 hover:bg-[#0d0a08]"
          >
            <EllipsisVerticalIcon className="h-5 w-5" />
          </button>
          {menuOpen ? (
            <div
              role="menu"
              className="absolute bottom-full right-0 z-20 mb-1 min-w-[10rem] rounded-xl border border-[#2a2030] bg-[#1a1520] py-1 shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              {!isArchived && onArchive ? (
                <button
                  type="button"
                  role="menuitem"
                  className="block w-full px-4 py-2 text-left text-sm text-[#F0E8D8] hover:bg-[#0d0a08]"
                  onClick={() => {
                    setMenuOpen(false);
                    onArchive();
                  }}
                >
                  Archive
                </button>
              ) : null}
              {onDelete ? (
                <button
                  type="button"
                  role="menuitem"
                  className="block w-full px-4 py-2 text-left text-sm text-rose-300 hover:bg-[#0d0a08]"
                  onClick={() => {
                    setMenuOpen(false);
                    onDelete();
                  }}
                >
                  Delete
                </button>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      {!isKids && !isArchived && observationModalOpen ? (
        <ConnectionTrendAssessmentModal
          personId={person.id}
          nickname={person.nickname}
          onComplete={loadConnectionTrendLatest}
          onClose={() => setObservationModalOpen(false)}
        />
      ) : null}
    </div>
  );
}
