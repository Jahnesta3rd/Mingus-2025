import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
} from 'react';

export interface ConnectionTrendBadgeProps {
  fadeTier: string;
  patternType: string | null;
  insightMessage: string | null;
}

const TIER_STYLES: Record<
  string,
  { label: string; className: string }
> = {
  locked_in: {
    label: '🔒 Locked In',
    className: 'bg-[#D1FAE5] text-emerald-800',
  },
  breadcrumbing: {
    label: '🍞 Breadcrumbing',
    className: 'bg-[#FEF9C3] text-[#D97706]',
  },
  orbiting: {
    label: '🪐 Orbiting',
    className: 'bg-[#FED7AA] text-orange-800',
  },
  fading: {
    label: '💨 Pulling a Fade',
    className: 'bg-[#FEE2E2] text-[#DC2626]',
  },
  dipping: {
    label: '📉 Dipping Out',
    className: 'bg-[#FECACA] text-red-900',
  },
  cloaking: {
    label: '🚫 Cloaking',
    className: 'bg-[#111827] text-white',
  },
};

const PATTERN_LABELS: Record<string, string> = {
  breadcrumber: 'Breadcrumber Pattern',
  classic_fade: 'Classic Fade Pattern',
  orbiter: 'Orbiter Pattern',
  casper: 'Casper Pattern',
};

function tierConfig(fadeTier: string) {
  return TIER_STYLES[fadeTier] ?? {
    label: fadeTier.replace(/_/g, ' '),
    className: 'bg-[#2a2030] text-[#F0E8D8]',
  };
}

/** Human-readable Fade Scale label for Connection Trend (e.g. roster banners). */
export function connectionTrendFadeTierLabel(fadeTier: string): string {
  return tierConfig(fadeTier).label;
}

export default function ConnectionTrendBadge({
  fadeTier,
  patternType,
  insightMessage,
}: ConnectionTrendBadgeProps) {
  const [mobileTipOpen, setMobileTipOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const tipId = useId();
  const cfg = tierConfig(fadeTier);
  const patternLabel =
    patternType && PATTERN_LABELS[patternType] ? PATTERN_LABELS[patternType] : null;
  const hasTip = Boolean(insightMessage);
  const tipToggleLabel = hasTip
    ? `${cfg.label}${patternLabel ? `, ${patternLabel}` : ''}. Show insight.`
    : undefined;

  useEffect(() => {
    if (!mobileTipOpen) return;
    const onDoc = (e: Event) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setMobileTipOpen(false);
      }
    };
    document.addEventListener('click', onDoc);
    return () => document.removeEventListener('click', onDoc);
  }, [mobileTipOpen]);

  const toggleMobileTip = (e: ReactMouseEvent | ReactKeyboardEvent) => {
    e.stopPropagation();
    if (!hasTip) return;
    setMobileTipOpen((o) => !o);
  };

  return (
    <div ref={wrapRef} className="group relative min-w-0 max-w-full">
      <div
        role={hasTip ? 'button' : undefined}
        tabIndex={hasTip ? 0 : undefined}
        aria-label={tipToggleLabel}
        className={`inline-flex max-w-full flex-col rounded-lg px-2.5 py-1.5 text-left text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-[#A78BFA] focus-visible:ring-offset-2 focus-visible:ring-offset-white ${cfg.className} ${hasTip ? 'min-h-11 min-w-[44px] cursor-pointer sm:min-h-0 sm:min-w-0 sm:cursor-default' : ''}`}
        onClick={(e) => {
          if (typeof window !== 'undefined' && window.matchMedia('(max-width: 639px)').matches) {
            toggleMobileTip(e);
          }
        }}
        onKeyDown={(e) => {
          if (!hasTip) return;
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (typeof window !== 'undefined' && window.matchMedia('(max-width: 639px)').matches) {
              toggleMobileTip(e);
            }
          }
        }}
        aria-expanded={hasTip ? mobileTipOpen : undefined}
        aria-describedby={hasTip ? tipId : undefined}
      >
        <span className="leading-snug">{cfg.label}</span>
        {patternLabel ? (
          <span className="mt-0.5 text-sm font-medium opacity-90">{patternLabel}</span>
        ) : null}
      </div>
      {hasTip && insightMessage ? (
        <div
          id={tipId}
          role="tooltip"
          className={`absolute left-0 top-full z-30 mt-1 max-w-[min(20rem,calc(100vw-2rem))] break-words rounded-lg border border-[#E2E8F0] bg-white p-3 text-sm leading-snug text-[#1E293B] shadow-lg sm:pointer-events-none sm:opacity-0 sm:transition-opacity sm:group-hover:pointer-events-auto sm:group-hover:opacity-100 ${
            mobileTipOpen ? 'block' : 'hidden'
          } sm:block`}
        >
          {insightMessage}
        </div>
      ) : null}
    </div>
  );
}
