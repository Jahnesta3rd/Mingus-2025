import React, { useState, useEffect, useCallback } from 'react';
import { Check } from 'lucide-react';

// ========================================
// TYPES
// ========================================

interface MilestoneItem {
  days: number;
  achieved: boolean;
  achieved_date: string | null;
}

interface MilestonesResponse {
  current_streak: number;
  next_milestone: number;
  milestones: MilestoneItem[];
  achievements: string[];
}

interface SpendingMilestonesWidgetProps {
  userId: string;
  className?: string;
}

const MILESTONE_DAYS = [3, 7, 14, 30, 60, 100] as const;
const PRIMARY_PURPLE = '#5B2D8E';

const MILESTONE_MESSAGES: Record<number, string> = {
  3: 'You started something. That is the hardest part. Keep going.',
  7: 'One week strong. Your future self is watching.',
  14: 'Two weeks in. Habits are forming. Stay consistent.',
  30: 'One month. You are building real financial discipline.',
  60: 'Two months. This is who you are now.',
  100: '100 days. You have built a foundation most people only dream about.',
};

// ========================================
// SVG CIRCULAR PROGRESS RING
// ========================================

function CircularStreakRing({
  currentStreak,
  nextMilestone,
  size = 120,
  strokeWidth = 6,
}: {
  currentStreak: number;
  nextMilestone: number;
  size?: number;
  strokeWidth?: number;
}) {
  const lastMilestone = MILESTONE_DAYS.filter((d) => d < nextMilestone).pop() ?? 0;
  const range = nextMilestone - lastMilestone;
  const progress = range <= 0 ? 100 : Math.min(100, ((currentStreak - lastMilestone) / range) * 100);

  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90" aria-hidden="true">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={PRIMARY_PURPLE}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        className="transition-[stroke-dashoffset] duration-500 ease-out"
      />
    </svg>
  );
}

// ========================================
// TOAST (dismissible, top-right of card, 4s)
// ========================================

function Toast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div
      className="absolute top-4 right-4 z-10 flex items-start gap-2 rounded-lg px-4 py-3 shadow-md"
      style={{ backgroundColor: '#f5f3ff' }}
      role="status"
    >
      <p className="text-sm text-gray-800 pr-6">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 rounded p-0.5"
        aria-label="Dismiss"
      >
        <span className="text-lg leading-none">×</span>
      </button>
    </div>
  );
}

// ========================================
// MILESTONE BADGE (with tooltip for achieved)
// ========================================

function MilestoneBadge({
  days,
  achieved,
  achievedDate,
}: {
  days: number;
  achieved: boolean;
  achievedDate: string | null;
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  const formattedDate =
    achievedDate != null
      ? new Date(achievedDate).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
      : '';

  return (
    <div className="relative flex flex-col items-center">
      <button
        type="button"
        className="flex flex-col items-center focus:outline-none focus:ring-2 focus:ring-offset-1 rounded-full focus:ring-[#5B2D8E]"
        onMouseEnter={() => achieved && setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        aria-label={achieved ? `Milestone ${days} days, achieved ${formattedDate}` : `${days} days milestone`}
      >
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold ${
            achieved
              ? 'border-[#5B2D8E] text-white'
              : 'border-gray-300 bg-white text-gray-500'
          }`}
          style={achieved ? { backgroundColor: PRIMARY_PURPLE } : undefined}
        >
          {achieved ? <Check className="h-5 w-5" strokeWidth={2.5} /> : days}
        </span>
        <span className="mt-1 text-xs text-gray-600">{days}d</span>
      </button>
      {showTooltip && achieved && formattedDate && (
        <div
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded bg-gray-900 text-white text-xs whitespace-nowrap z-20"
          role="tooltip"
        >
          {formattedDate}
        </div>
      )}
    </div>
  );
}

// ========================================
// MAIN COMPONENT
// ========================================

export default function SpendingMilestonesWidget({
  userId,
  className = '',
}: SpendingMilestonesWidgetProps) {
  const [data, setData] = useState<MilestonesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchMilestones = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('mingus_token');
      const response = await fetch(
        `/api/gamification/milestones?userId=${encodeURIComponent(userId)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch milestone data');
      }

      const json: MilestonesResponse = await response.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load milestone data');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchMilestones();
  }, [fetchMilestones]);

  // Show toast when a milestone was achieved today (only on first render with data)
  useEffect(() => {
    if (data == null || toastMessage != null) return;
    const today = new Date().toISOString().slice(0, 10);
    const achievedToday = data.milestones.find(
      (m) => m.achieved && m.achieved_date != null && m.achieved_date.slice(0, 10) === today
    );
    if (achievedToday != null && data.current_streak === achievedToday.days) {
      const message = MILESTONE_MESSAGES[achievedToday.days as keyof typeof MILESTONE_MESSAGES];
      if (message) setToastMessage(message);
    }
  }, [data, toastMessage]);

  // Loading: skeleton card
  if (loading) {
    return (
      <div
        className={`rounded-xl bg-white p-6 shadow-sm ${className}`}
        role="status"
        aria-label="Loading milestone data"
      >
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 bg-gray-200 rounded" />
          <div className="flex flex-col sm:flex-row gap-6">
            <div className="flex flex-col items-center sm:items-start space-y-3">
              <div className="h-24 w-24 rounded-full bg-gray-200" />
              <div className="h-4 w-20 bg-gray-200 rounded" />
              <div className="h-4 w-28 bg-gray-200 rounded" />
            </div>
            <div className="flex-1 flex gap-2 justify-around">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-10 w-10 rounded-full bg-gray-200" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error: message + retry
  if (error) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
        <p className="text-gray-700 mb-4">Unable to load milestone data</p>
        <button
          type="button"
          onClick={fetchMilestones}
          className="rounded-lg px-4 py-2 text-white transition-colors hover:opacity-90"
          style={{ backgroundColor: PRIMARY_PURPLE }}
        >
          Retry
        </button>
      </div>
    );
  }

  // Empty: no streak yet
  if (data != null && data.current_streak === 0) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
        <p className="text-gray-700 mb-4">Complete your first check-in to start your streak</p>
        <a
          href="/daily-outlook"
          className="inline-block rounded-lg px-4 py-2 text-white transition-colors hover:opacity-90"
          style={{ backgroundColor: PRIMARY_PURPLE }}
        >
          Go to Daily Outlook
        </a>
      </div>
    );
  }

  if (data == null) return null;

  const milestoneByDays = Object.fromEntries(data.milestones.map((m) => [m.days, m]));

  return (
    <div className={`relative rounded-xl bg-white p-6 shadow-sm ${className}`} role="region" aria-label="Spending milestones">
      {toastMessage != null && (
        <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-6">
        {/* LEFT — Streak counter + ring */}
        <div className="flex flex-col items-center sm:items-start">
          <div className="relative flex items-center justify-center">
            <CircularStreakRing
              currentStreak={data.current_streak}
              nextMilestone={data.next_milestone}
              size={120}
              strokeWidth={6}
            />
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-gray-900 tabular-nums">
                {data.current_streak}
              </span>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-600">day streak</p>
          <p className="text-sm text-gray-500">Next milestone: {data.next_milestone} days</p>
        </div>

        {/* RIGHT — Badge row */}
        <div className="flex-1 flex flex-wrap items-center justify-center sm:justify-around gap-4 sm:gap-2">
          {MILESTONE_DAYS.map((days) => {
            const m = milestoneByDays[days];
            return (
              <MilestoneBadge
                key={days}
                days={days}
                achieved={m?.achieved ?? false}
                achievedDate={m?.achieved_date ?? null}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
