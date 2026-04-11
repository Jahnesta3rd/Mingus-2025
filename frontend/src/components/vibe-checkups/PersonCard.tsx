import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  EllipsisVerticalIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusSmallIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import type { VibePersonAssessment, VibePersonTrend, VibeTrackedPerson } from '../../hooks/useVibeTracker';

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
          className="h-full rounded-full bg-[#C4A064]"
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
  isArchived?: boolean;
  onArchive?: () => void;
  onDelete?: () => void;
  onRestore?: () => void;
};

export function PersonCard({
  person,
  trend,
  latestAssessment,
  onClick,
  isArchived = false,
  onArchive,
  onDelete,
  onRestore,
}: PersonCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

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
      className="relative cursor-pointer rounded-2xl border border-[#2a2030] bg-[#1a1520]/90 p-4 text-left shadow-lg outline-none ring-[#C4A064]/30 transition hover:border-[#C4A064]/35 focus-visible:ring-2"
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#0d0a08] text-2xl"
          aria-hidden
        >
          {person.emoji || '·'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-display text-base font-semibold text-[#F0E8D8]">{person.nickname}</h3>
            <span className="shrink-0 rounded-full border border-[#2a2030] bg-[#0d0a08] px-2 py-0.5 text-[10px] font-medium tabular-nums text-[#C4A064]">
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
        </div>
      </div>

      {hasScores ? (
        <div className="mt-4 space-y-2" onClick={(e) => e.stopPropagation()}>
          <MiniBar value={emo} label="Emotional" />
          <MiniBar value={fin} label="Financial" />
        </div>
      ) : (
        <p className="mt-3 text-xs text-[#9a8f7e]">Complete a checkup to see scores here.</p>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#2a2030]/80 pt-3">
        <TrendGlyph trend={trend} />
        <span className="text-xs text-[#9a8f7e]">Last assessed: {formatRelativePast(person.last_assessed_at)}</span>
      </div>

      <div className="mt-4 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
        {isArchived ? (
          <button
            type="button"
            onClick={() => onRestore?.()}
            className="flex-1 rounded-xl border border-[#C4A064] bg-transparent py-2.5 text-sm font-semibold text-[#C4A064] transition hover:bg-[#C4A064]/10"
          >
            Restore
          </button>
        ) : (
          <Link
            to="/dashboard/vibe-checkups"
            className="flex-1 rounded-xl border border-[#C4A064]/60 bg-transparent py-2.5 text-center text-sm font-semibold text-[#C4A064] transition hover:border-[#C4A064] hover:bg-[#C4A064]/10"
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
            className="rounded-lg border border-[#2a2030] p-2 text-[#F0E8D8] transition hover:border-[#C4A064]/40 hover:bg-[#0d0a08]"
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
    </div>
  );
}
