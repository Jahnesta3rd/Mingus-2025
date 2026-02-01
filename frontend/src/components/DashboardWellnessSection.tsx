import React, { useState, useCallback } from 'react';
import {
  CheckinReminderBanner,
  WellnessScoreCard,
  WellnessImpactCard,
  WeeklyCheckinForm,
} from './wellness';
import type { WellnessScores } from './wellness/WellnessScoreCard';
import type { WellnessInsight } from './wellness/InsightCard';
import type { CheckinResponse } from './wellness/types';
import { useWellnessData } from '../hooks/useWellnessData';
import { RefreshCw } from 'lucide-react';

export interface DashboardWellnessSectionProps {
  className?: string;
}

/**
 * Dashboard wellness block: reminder banner (if due), score card, impact card.
 * Loading skeletons and error with retry. Check-in modal with refetch on success.
 */
export const DashboardWellnessSection: React.FC<DashboardWellnessSectionProps> = ({
  className = '',
}) => {
  const {
    scores: scoresRaw,
    insights,
    streak,
    currentWeekCheckin,
    weeksOfData,
    loading,
    error,
    refetch,
  } = useWellnessData();

  const [checkinModalOpen, setCheckinModalOpen] = useState(false);
  const [checkinSuccessMessage, setCheckinSuccessMessage] = useState<string | null>(null);

  const lastCheckinDate = currentWeekCheckin
    ? currentWeekCheckin.week_ending_date
    : (streak?.last_checkin_date ?? null);
  const currentStreak = streak?.current_streak ?? 0;
  const weeks = weeksOfData || streak?.total_checkins ?? 0;

  const scoresForCard: WellnessScores | null = scoresRaw
    ? {
        physical_score: scoresRaw.physical_score ?? 0,
        mental_score: scoresRaw.mental_score ?? 0,
        relational_score: scoresRaw.relational_score ?? 0,
        financial_feeling_score: scoresRaw.financial_feeling_score ?? 0,
        overall_wellness_score: scoresRaw.overall_wellness_score ?? 0,
        physical_change: scoresRaw.physical_change ?? 0,
        mental_change: scoresRaw.mental_change ?? 0,
        relational_change: scoresRaw.relational_change ?? 0,
        overall_change: scoresRaw.overall_change ?? 0,
        week_ending_date: scoresRaw.week_ending_date ?? '',
      }
    : null;

  const insightsForCard: WellnessInsight[] = (insights ?? []).map((i) => ({
    type: (i.type ?? 'recommendation') as WellnessInsight['type'],
    title: i.title ?? '',
    message: i.message ?? '',
    data_backing: i.data_backing ?? '',
    action: i.action ?? '',
    priority: typeof i.priority === 'number' ? i.priority : 0,
    category: (i.category ?? 'financial') as WellnessInsight['category'],
    dollar_amount: i.dollar_amount,
  }));

  const handleStartCheckin = useCallback(() => {
    setCheckinModalOpen(true);
    setCheckinSuccessMessage(null);
  }, []);

  const handleCheckinSuccess = useCallback(
    (response: CheckinResponse) => {
      setCheckinSuccessMessage('Check-in complete! Your wellness scores have been updated.');
      refetch();
      setCheckinModalOpen(false);
    },
    [refetch]
  );

  const handleCheckinClose = useCallback(() => {
    setCheckinModalOpen(false);
    setCheckinSuccessMessage(null);
  }, []);

  const handleDismissReminder = useCallback(() => {
    // Banner handles its own 24h dismiss in localStorage
  }, []);

  const showReminder = !currentWeekCheckin;

  if (error) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
        role="region"
        aria-label="Wellness section"
      >
        <p className="text-slate-300 font-medium mb-2">Unable to load wellness data</p>
        <p className="text-slate-400 text-sm mb-4">{error}</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 min-h-[44px] px-4 rounded-xl font-semibold bg-violet-600 text-white hover:bg-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          aria-label="Retry loading wellness data"
        >
          <RefreshCw className="w-4 h-4" aria-hidden />
          Retry
        </button>
      </div>
    );
  }

  return (
    <section className={`space-y-6 ${className}`} aria-label="Wellness">
      {checkinSuccessMessage && (
        <div
          className="rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 px-4 py-3 text-sm font-medium"
          role="status"
          aria-live="polite"
        >
          {checkinSuccessMessage}
        </div>
      )}

      {showReminder && (
        <CheckinReminderBanner
          lastCheckinDate={lastCheckinDate}
          currentStreak={currentStreak}
          weeksOfData={weeks}
          onStartCheckin={handleStartCheckin}
          onDismiss={handleDismissReminder}
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <>
            <WellnessScoreCardSkeleton />
            <WellnessImpactCardSkeleton />
          </>
        ) : (
          <>
            <WellnessScoreCard
              scores={scoresForCard}
              onStartCheckin={handleStartCheckin}
            />
            <WellnessImpactCard
              insights={insightsForCard}
              weeksOfData={weeks}
            />
          </>
        )}
      </div>

      {checkinModalOpen && (
        <CheckinModal
          onClose={handleCheckinClose}
          onSuccess={handleCheckinSuccess}
        />
      )}
    </section>
  );
};

function WellnessScoreCardSkeleton() {
  return (
    <div
      className="rounded-2xl bg-slate-800/80 border border-slate-700 p-6 animate-pulse"
      role="status"
      aria-label="Loading wellness score"
    >
      <div className="flex flex-col items-center mb-8">
        <div className="w-40 h-40 rounded-full bg-slate-700 mb-4" />
        <div className="h-6 w-24 bg-slate-700 rounded mb-2" />
        <div className="h-4 w-32 bg-slate-700 rounded mb-6" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-slate-700 rounded-xl" />
        ))}
      </div>
      <span className="sr-only">Loading wellness score…</span>
    </div>
  );
}

function WellnessImpactCardSkeleton() {
  return (
    <div
      className="rounded-2xl bg-slate-800/80 border border-slate-700 p-6 animate-pulse"
      role="status"
      aria-label="Loading wellness insights"
    >
      <div className="h-6 w-48 bg-slate-700 rounded mb-6" />
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-slate-700 rounded-xl" />
        ))}
      </div>
      <span className="sr-only">Loading wellness insights…</span>
    </div>
  );
}

interface CheckinModalProps {
  onClose: () => void;
  onSuccess: (response: CheckinResponse) => void;
}

function CheckinModal({ onClose, onSuccess }: CheckinModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkin-modal-title"
    >
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-slate-800 border border-slate-700 shadow-xl">
        <div className="sticky top-0 flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800 z-10">
          <h2 id="checkin-modal-title" className="text-lg font-bold text-slate-100">
            Weekly Check-in
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="p-4">
          <WeeklyCheckinForm
            onSuccess={onSuccess}
            onCancel={onClose}
          />
        </div>
      </div>
    </div>
  );
}

export default DashboardWellnessSection;
