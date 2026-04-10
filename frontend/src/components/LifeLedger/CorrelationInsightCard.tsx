import React from 'react';

export interface CorrelationInsightCardProps {
  correlation: {
    type: string;
    strength: string;
    description: string;
    insight_message: string;
  };
  /** Months of history this insight draws from (footer copy). */
  monthsApprox?: number;
  /** When true, card is non-interactive and used as a locked preview placeholder. */
  blurred?: boolean;
}

function patternIcon(type: string): string {
  const t = type.toUpperCase();
  if (t.includes('FITNESS')) return '💪';
  if (t.includes('FINANCIAL')) return '💰';
  if (t.includes('WELLNESS')) return '🧠';
  if (t.includes('OVERALL')) return '📈';
  return '📈';
}

function strengthLabel(strength: string): { text: string; className: string } {
  const s = strength.toLowerCase();
  if (s === 'strong') {
    return { text: 'Strong pattern', className: 'bg-[#C4A064]/20 text-[#C4A064] border border-[#C4A064]/40' };
  }
  if (s === 'moderate') {
    return { text: 'Moderate', className: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' };
  }
  return { text: 'Mild', className: 'bg-[#F0E8D8]/10 text-[#F0E8D8] border border-[#9a8f7e]/40' };
}

const CorrelationInsightCard: React.FC<CorrelationInsightCardProps> = ({
  correlation,
  monthsApprox = 6,
  blurred = false,
}) => {
  const badge = strengthLabel(correlation.strength);
  const n = Math.max(1, monthsApprox);

  return (
    <div
      className={`relative rounded-lg border border-[#9a8f7e]/25 bg-[#1a1512]/90 pl-4 pr-4 py-3 shadow-sm ${
        blurred ? 'select-none overflow-hidden' : ''
      }`}
      style={{ borderLeftWidth: '4px', borderLeftColor: '#C4A064' }}
    >
      {blurred && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center bg-[#0d0a08]/55 backdrop-blur-sm px-4 text-center text-sm font-medium text-[#F0E8D8]"
          aria-hidden
        >
          Upgrade to Professional to see all patterns
        </div>
      )}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xl shrink-0" aria-hidden>
            {patternIcon(correlation.type)}
          </span>
          <p className="text-sm font-medium text-[#C4A064] leading-snug">{correlation.description}</p>
        </div>
        <span className={`text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded shrink-0 ${badge.className}`}>
          {badge.text}
        </span>
      </div>
      <p className="mt-2 text-[15px] leading-relaxed text-[#F0E8D8]">{correlation.insight_message}</p>
      <p className="mt-3 text-xs text-[#9a8f7e]">Based on your last {n} months of data</p>
    </div>
  );
};

export default CorrelationInsightCard;
