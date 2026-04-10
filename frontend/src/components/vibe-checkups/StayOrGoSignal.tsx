import type { VibePersonTrend } from '../../hooks/useVibeTracker';

export type StayOrGoSignalProps = {
  trend: VibePersonTrend;
};

function confidenceLabel(c: number | null | undefined): string {
  if (c == null || Number.isNaN(c)) return '';
  const pct = c <= 1 ? Math.round(c * 100) : Math.round(c);
  return `${pct}% confidence`;
}

function buildExplanation(trend: VibePersonTrend): string[] {
  const n = trend.assessment_count;
  const ed = trend.emotional_delta;
  const fd = trend.financial_delta;
  const dir = trend.trend_direction;

  const emoPhrase =
    ed == null
      ? 'Emotional compatibility has been steady across your checkups.'
      : ed > 3
        ? `Their emotional compatibility has improved by about ${ed} points over ${n} checkups.`
        : ed < -3
          ? `Emotional compatibility has slipped by about ${Math.abs(ed)} points across ${n} checkups.`
          : `Emotional scores have stayed in a similar range over ${n} checkups.`;

  const finPhrase =
    fd == null
      ? 'Financial alignment looks similar to where you started.'
      : fd > 3
        ? `Financial match has moved up by about ${fd} points.`
        : fd < -3
          ? `Financial match has moved down by about ${Math.abs(fd)} points.`
          : 'Financial match has been fairly steady.';

  const tail =
    dir === 'improving'
      ? 'The overall pattern is moving in a warmer direction.'
      : dir === 'declining'
        ? 'The overall pattern has cooled compared with your first checkup.'
        : 'Signals are mixed week to week — keep checking in as things evolve.';

  return [emoPhrase, finPhrase, tail];
}

export function StayOrGoSignal({ trend }: StayOrGoSignalProps) {
  if (trend.assessment_count < 3) {
    return null;
  }

  const signal = trend.stay_or_go_signal ?? 'neutral';
  const conf = confidenceLabel(trend.stay_or_go_confidence);
  const paras = buildExplanation(trend);

  if (signal === 'too_early') {
    return (
      <div className="mt-6 space-y-3 rounded-2xl border border-[#2a2030] bg-[#0d0a08] px-5 py-5 text-left">
        <p className="font-display text-lg font-semibold text-[#F0E8D8]">⏳ Check in a few more times.</p>
        {conf ? <p className="text-xs text-[#9a8f7e]">{conf}</p> : null}
        <p className="text-sm leading-relaxed text-[#F0E8D8]/85">{paras.join(' ')}</p>
        <p className="text-[11px] leading-relaxed text-[#9a8f7e]">Based on your responses. Trust your instincts.</p>
      </div>
    );
  }

  if (signal === 'stay') {
    return (
      <div className="mt-6 space-y-3 rounded-2xl border border-emerald-800/50 bg-emerald-950/40 px-5 py-5 text-left">
        <p className="font-display text-lg font-semibold text-emerald-100">🌿 The data says stay.</p>
        {conf ? <p className="text-xs text-emerald-200/60">{conf}</p> : null}
        {paras.map((p, i) => (
          <p key={i} className="text-sm leading-relaxed text-emerald-50/90">
            {p}
          </p>
        ))}
        <p className="text-[11px] leading-relaxed text-emerald-200/50">Based on your responses. Trust your instincts.</p>
      </div>
    );
  }

  if (signal === 'go') {
    return (
      <div className="mt-6 space-y-3 rounded-2xl border border-rose-900/50 bg-rose-950/35 px-5 py-5 text-left">
        <p className="font-display text-lg font-semibold text-rose-100">🚩 The pattern says go.</p>
        {conf ? <p className="text-xs text-rose-200/60">{conf}</p> : null}
        {paras.map((p, i) => (
          <p key={i} className="text-sm leading-relaxed text-rose-50/90">
            {p}
          </p>
        ))}
        <p className="text-[11px] leading-relaxed text-rose-200/50">Based on your responses. Trust your instincts.</p>
      </div>
    );
  }

  /* neutral */
  return (
    <div className="mt-6 space-y-3 rounded-2xl border border-amber-900/40 bg-amber-950/30 px-5 py-5 text-left">
      <p className="font-display text-lg font-semibold text-amber-100">⚖️ Mixed signals.</p>
      {conf ? <p className="text-xs text-amber-200/60">{conf}</p> : null}
      {paras.map((p, i) => (
        <p key={i} className="text-sm leading-relaxed text-amber-50/90">
          {p}
        </p>
      ))}
      <p className="text-[11px] leading-relaxed text-amber-200/50">Based on your responses. Trust your instincts.</p>
    </div>
  );
}
