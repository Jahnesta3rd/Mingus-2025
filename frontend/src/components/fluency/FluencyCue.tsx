import React, { useCallback, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, X } from 'lucide-react';
import { FLUENCY_CUES } from './fluencyCueConfig';
import type { FluencyCueEntry, FluencyDomain, UserTier, WaterfallContext } from './types';

const MIN_DATA_COMPLETENESS = 0.2;

function isoWeekNumber(date = new Date()): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

function tierMatches(cueTier: FluencyCueEntry['tier'], userTier: string): boolean {
  if (cueTier === 'all') return true;
  return cueTier === userTier;
}

function triggerMatches(cue: FluencyCueEntry, context: WaterfallContext): boolean {
  const value = context[cue.triggerField];
  return value === cue.triggerValue;
}

function isDismissed(cueId: string): boolean {
  try {
    const week = isoWeekNumber();
    return localStorage.getItem(`fluency_dismissed_${cueId}_${week}`) === '1';
  } catch {
    return false;
  }
}

function dismissCue(cueId: string): void {
  try {
    const week = isoWeekNumber();
    localStorage.setItem(`fluency_dismissed_${cueId}_${week}`, '1');
  } catch {
    /* ignore quota / private mode */
  }
}

export interface FluencyCueProps {
  context: WaterfallContext;
  domain: FluencyDomain | string;
  userTier: UserTier | string;
  /** Called when user taps an action CTA — wrapper should navigate immediately. */
  onActionRoute?: (route: string) => void;
}

export const FluencyCue: React.FC<FluencyCueProps> = ({
  context,
  domain,
  userTier,
  onActionRoute,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const cue = useMemo(() => {
    if (context.data_completeness < MIN_DATA_COMPLETENESS) {
      return null;
    }
    return (
      FLUENCY_CUES.find(
        (entry) =>
          entry.domain === domain &&
          tierMatches(entry.tier, userTier) &&
          triggerMatches(entry, context) &&
          !isDismissed(entry.id)
      ) ?? null
    );
  }, [context, domain, userTier]);

  const handleDismiss = useCallback(() => {
    if (!cue) return;
    dismissCue(cue.id);
    setDismissed(true);
  }, [cue]);

  const handleAction = useCallback(() => {
    if (!cue?.actionRoute || !onActionRoute) return;
    onActionRoute(cue.actionRoute);
  }, [cue, onActionRoute]);

  if (!cue || dismissed) {
    return null;
  }

  const showBody = cue.expandable ? expanded && cue.body : cue.body;

  return (
    <div
      className="relative rounded-xl border-l-4 px-4 py-3 pr-10"
      style={{
        background: 'var(--soft-purple, #EDE9FE)',
        borderLeftColor: 'var(--mingus-purple, #5b2d8e)',
        borderTop: '1px solid var(--line, #e8e1f0)',
        borderRight: '1px solid var(--line, #e8e1f0)',
        borderBottom: '1px solid var(--line, #e8e1f0)',
        fontFamily: 'Manrope, system-ui, sans-serif',
      }}
      role="status"
    >
      <button
        type="button"
        onClick={handleDismiss}
        className="absolute right-2 top-2 inline-flex min-h-8 min-w-8 items-center justify-center rounded-lg text-[var(--ink-mid,#5c5751)] transition hover:bg-white/60"
        aria-label="Dismiss cue"
      >
        <X className="h-4 w-4" aria-hidden />
      </button>

      <p className="text-xs font-medium" style={{ color: 'var(--ink-mid, #5c5751)' }}>
        Why this matters
      </p>

      {cue.expandable ? (
        <button
          type="button"
          onClick={() => setExpanded((o) => !o)}
          className="mt-1 flex w-full items-start gap-2 text-left"
          aria-expanded={expanded}
        >
          <p className="flex-1 text-sm leading-snug" style={{ color: 'var(--ink, #1a1815)' }}>
            {cue.headline}
          </p>
          <span className="mt-0.5 shrink-0 text-[var(--mingus-purple,#5b2d8e)]">
            {expanded ? (
              <ChevronUp className="h-4 w-4" aria-hidden />
            ) : (
              <ChevronDown className="h-4 w-4" aria-hidden />
            )}
          </span>
        </button>
      ) : (
        <p className="mt-1 text-sm leading-snug" style={{ color: 'var(--ink, #1a1815)' }}>
          {cue.headline}
        </p>
      )}

      {showBody ? (
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink-mid, #5c5751)' }}>
          {cue.body}
        </p>
      ) : null}

      {cue.actionLabel && cue.actionRoute ? (
        <button
          type="button"
          onClick={handleAction}
          className="mt-3 text-sm font-semibold transition hover:underline"
          style={{ color: 'var(--mingus-purple, #5b2d8e)' }}
        >
          {cue.actionLabel}
        </button>
      ) : null}
    </div>
  );
};

export default FluencyCue;
