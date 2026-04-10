import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { useFeatureTrack } from '../hooks/useFeatureTrack';
import { useAuth } from '../hooks/useAuth';
import { trackEvent } from '../utils/trackEvent';
import { CheckInForm } from '../components/spirit/CheckInForm';
import { PracticeCalendar } from '../components/spirit/PracticeCalendar';
import { StreakBadge } from '../components/spirit/StreakBadge';
import { SuccessModal } from '../components/spirit/SuccessModal';
import type { SubmitCheckinResult } from '../hooks/useSpiritCheckin';
import { CorrelationView } from '../components/spirit/CorrelationView';
import { HistoryView } from '../components/spirit/HistoryView';
import { InsightsView } from '../components/spirit/InsightsView';
import { TierGateOverlay } from '../components/spirit/TierGateOverlay';

type SpiritTab = 'daily' | 'correlation' | 'history' | 'insights';

type EffectiveTier = 'budget' | 'mid_tier' | 'professional';

function effectiveUserTier(user: { tier?: string; is_beta?: boolean } | null): EffectiveTier {
  if (user?.is_beta) return 'professional';
  const t = (user?.tier || 'budget').trim().toLowerCase();
  if (t === 'professional') return 'professional';
  if (t === 'mid_tier') return 'mid_tier';
  return 'budget';
}

type TierGateTarget = { requiredTier: 'mid_tier' | 'professional'; feature: string };

export default function SpiritFinance() {
  useFeatureTrack('spirit_finance_dashboard');
  const { user } = useAuth();
  const userTier = useMemo(() => effectiveUserTier(user), [user]);
  const canHistory = userTier === 'mid_tier' || userTier === 'professional';
  const canInsights = userTier === 'professional';

  const [tab, setTab] = useState<SpiritTab>('daily');
  const [seenCorrelation, setSeenCorrelation] = useState(false);
  const [seenHistory, setSeenHistory] = useState(false);
  const [seenInsights, setSeenInsights] = useState(false);
  const [tierGate, setTierGate] = useState<TierGateTarget | null>(null);
  const [successOpen, setSuccessOpen] = useState(false);
  const [successPayload, setSuccessPayload] = useState<{
    practiceType: string;
    practiceScore: number;
    streak: number;
  } | null>(null);

  const month = useMemo(() => {
    const t = new Date();
    return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}`;
  }, []);

  const tabs: { id: SpiritTab; label: string }[] = [
    { id: 'daily', label: 'Daily Check-In' },
    { id: 'correlation', label: 'Correlation' },
    { id: 'history', label: 'History' },
    { id: 'insights', label: 'Insights' },
  ];

  const handleTabSelect = (id: SpiritTab) => {
    if (id === 'history' && !canHistory) {
      setTierGate({ requiredTier: 'mid_tier', feature: 'Spirit history' });
      return;
    }
    if (id === 'insights' && !canInsights) {
      setTierGate({ requiredTier: 'professional', feature: 'Spirit insights' });
      return;
    }
    setTab(id);
    if (id === 'correlation') setSeenCorrelation(true);
    if (id === 'history') setSeenHistory(true);
    if (id === 'insights') setSeenInsights(true);
  };

  const handleCheckinSuccess = (result: SubmitCheckinResult) => {
    void trackEvent('spirit_checkin', 'click');
    setSuccessPayload({
      practiceType: result.checkin.practice_type,
      practiceScore: result.practice_score,
      streak: result.streak.current_streak,
    });
    setSuccessOpen(true);
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#FFF8EC] px-4 py-8 text-[#0f172a] sm:px-6 lg:px-8">
      <div
        className={`mx-auto ${tab === 'history' || tab === 'insights' ? 'max-w-6xl' : 'max-w-3xl'}`}
      >
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link
              to="/dashboard"
              className="text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
            >
              ← Main dashboard
            </Link>
            <h1 className="mt-2 font-display text-2xl font-semibold text-[#0f172a] sm:text-3xl">
              Spirit & Finance
            </h1>
            <p className="mt-1 text-sm text-slate-600">Daily practice check-in and financial calm.</p>
          </div>
          <StreakBadge className="self-start sm:self-center" />
        </div>

        <div className="mb-8 border-b border-slate-200">
          <nav className="-mb-px flex gap-1 overflow-x-auto sm:gap-4" aria-label="Spirit sections">
            {tabs.map((t) => {
              const lockedHistory = t.id === 'history' && !canHistory;
              const lockedInsights = t.id === 'insights' && !canInsights;
              const locked = lockedHistory || lockedInsights;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => handleTabSelect(t.id)}
                  className={`inline-flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition-colors sm:px-4 ${
                    tab === t.id
                      ? 'border-[#C4A064] text-[#0f172a]'
                      : locked
                        ? 'border-transparent text-slate-400 hover:border-slate-200 hover:text-slate-500'
                        : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
                  }`}
                  aria-disabled={locked}
                >
                  {locked ? <Lock className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden /> : null}
                  {t.label}
                </button>
              );
            })}
          </nav>
        </div>

        {tab === 'daily' && (
          <div className="space-y-8">
            <CheckInForm onSuccess={handleCheckinSuccess} />
            <PracticeCalendar month={month} userId={user?.id} />
          </div>
        )}
        {seenCorrelation && (
          <div
            className={tab === 'correlation' ? '' : 'hidden'}
            aria-hidden={tab !== 'correlation'}
          >
            <CorrelationView userTier={userTier} isBeta={false} />
          </div>
        )}
        {seenHistory && (
          <div className={tab === 'history' ? '' : 'hidden'} aria-hidden={tab !== 'history'}>
            <HistoryView />
          </div>
        )}
        {seenInsights && (
          <div className={tab === 'insights' ? '' : 'hidden'} aria-hidden={tab !== 'insights'}>
            <InsightsView userTier={userTier} isBeta={false} />
          </div>
        )}
      </div>

      {tierGate && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="presentation"
          onClick={() => setTierGate(null)}
        >
          <div
            className="relative h-72 w-full max-w-md overflow-hidden rounded-xl border border-[#C4A064]/30 shadow-xl"
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <TierGateOverlay
              requiredTier={tierGate.requiredTier}
              feature={tierGate.feature}
              onDismiss={() => setTierGate(null)}
              className="!rounded-xl"
            />
          </div>
        </div>
      )}

      {successPayload && (
        <SuccessModal
          isOpen={successOpen}
          onClose={() => {
            setSuccessOpen(false);
            setSuccessPayload(null);
          }}
          practiceType={successPayload.practiceType}
          practiceScore={successPayload.practiceScore}
          streak={successPayload.streak}
        />
      )}
    </div>
  );
}
