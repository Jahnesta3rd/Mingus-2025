import React, { useState, useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import { StreakCounter } from './StreakCounter';
import { InsightUnlockProgress } from './InsightUnlockProgress';

const DISMISS_KEY = 'mingus_checkin_reminder_dismissed_until';
const DISMISS_HOURS = 24;

function getWeekEnding(d: Date): Date {
  const copy = new Date(d);
  const day = copy.getDay();
  const daysToSunday = day === 0 ? 0 : 7 - day;
  copy.setDate(copy.getDate() + daysToSunday);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function isSameWeek(d1: Date, d2: Date): boolean {
  const sun1 = getWeekEnding(d1).toDateString();
  const sun2 = getWeekEnding(d2).toDateString();
  return sun1 === sun2;
}

function isCompletedThisWeek(lastCheckinDate: string | null): boolean {
  if (!lastCheckinDate) return false;
  try {
    const last = new Date(lastCheckinDate);
    const today = new Date();
    return isSameWeek(last, today);
  } catch {
    return false;
  }
}

function isMonday(): boolean {
  return new Date().getDay() === 1;
}

export type ReminderState = 'never' | 'building' | 'due' | 'streak_at_risk' | 'completed';

export interface CheckinReminderBannerProps {
  lastCheckinDate: string | null;
  currentStreak: number;
  weeksOfData: number;
  onStartCheckin: () => void;
  onDismiss: () => void;
  className?: string;
}

/**
 * Reminder banner: prompts for weekly check-in. States for never, building,
 * due, streak-at-risk. Dismissible for 24h (localStorage). Slide-in + CTA bounce.
 */
export const CheckinReminderBanner: React.FC<CheckinReminderBannerProps> = ({
  lastCheckinDate,
  currentStreak,
  weeksOfData,
  onStartCheckin,
  onDismiss,
  className = '',
}) => {
  const [dismissedUntil, setDismissedUntil] = useState<number>(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DISMISS_KEY);
      if (raw) setDismissedUntil(parseInt(raw, 10) || 0);
    } catch {
      // ignore
    }
    setMounted(true);
  }, []);

  const handleDismiss = useCallback(() => {
    const until = Date.now() + DISMISS_HOURS * 60 * 60 * 1000;
    setDismissedUntil(until);
    try {
      localStorage.setItem(DISMISS_KEY, String(until));
    } catch {
      // ignore
    }
    onDismiss();
  }, [onDismiss]);

  const completedThisWeek = isCompletedThisWeek(lastCheckinDate);
  const now = Date.now();
  const isDismissed = dismissedUntil > now;

  const state: ReminderState = (() => {
    if (completedThisWeek) return 'completed';
    if (lastCheckinDate === null) return 'never';
    if (isMonday() && currentStreak >= 1) return 'streak_at_risk';
    if (weeksOfData >= 1 && weeksOfData <= 3) return 'building';
    return 'due';
  })();

  if (state === 'completed') return null;
  if (isDismissed) return null;

  const content = (() => {
    switch (state) {
      case 'never':
        return {
          title: 'Start Your Wellness Journey',
          subtitle: 'Take 7 minutes to complete your first check-in. Track your wellness AND spending to discover patterns.',
          cta: 'Start Check-in',
          ctaUrgent: false,
        };
      case 'building':
        return {
          title: 'Keep Building Your Profile',
          subtitle: null,
          cta: 'Continue Building',
          ctaUrgent: false,
        };
      case 'due':
        return {
          title: 'Weekly Check-in Time!',
          subtitle: "How was your week? Let's track your wellness and spending.",
          cta: 'Complete Check-in',
          ctaUrgent: false,
        };
      case 'streak_at_risk':
        return {
          title: `Don't break your ${currentStreak}-week streak!`,
          subtitle: 'Complete your check-in before midnight to keep your streak alive!',
          cta: 'Save My Streak',
          ctaUrgent: true,
        };
      default:
        return { title: '', subtitle: '', cta: 'Check-in', ctaUrgent: false };
    }
  })();

  return (
    <div
      className={`
        relative rounded-xl overflow-hidden
        bg-gradient-to-r from-violet-600 to-indigo-600
        text-white p-4 pr-12
        ${mounted ? 'animate-slide-in-banner' : 'opacity-0 -translate-y-4'}
        ${className}
      `}
      role="region"
      aria-label="Weekly check-in reminder"
    >
      <button
        type="button"
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/50"
        aria-label="Dismiss reminder for 24 hours"
      >
        <X className="w-5 h-5" aria-hidden />
      </button>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-white">
            {state === 'streak_at_risk' && currentStreak > 2 && (
              <span className="inline-flex items-center gap-1.5 mr-1" aria-hidden>
                <StreakCounter count={currentStreak} animate />
              </span>
            )}
            {state === 'streak_at_risk' && currentStreak <= 2 && '🔥 '}
            {state !== 'streak_at_risk' && (state === 'never' ? '🌟 ' : '📝 ')}
            {content.title}
          </h3>
          {content.subtitle && (
            <p className="text-white/90 text-sm mt-1">{content.subtitle}</p>
          )}
          {state === 'building' && (
            <p className="text-white/90 text-sm mt-1">
              Check-in #{weeksOfData + 1} —{' '}
              <InsightUnlockProgress weeksOfData={weeksOfData} compact />
            </p>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {state === 'building' && weeksOfData < 4 && (
            <div className="hidden sm:block">
              <InsightUnlockProgress weeksOfData={weeksOfData} />
            </div>
          )}
          <button
            type="button"
            onClick={onStartCheckin}
            className={`
              min-h-[44px] px-6 rounded-xl font-semibold
              focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-violet-600
              ${content.ctaUrgent
                ? 'bg-amber-400 text-amber-900 hover:bg-amber-300 animate-bounce-slow'
                : 'bg-white text-violet-700 hover:bg-white/90'
              }
            `}
            aria-label={content.cta}
          >
            {content.cta}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CheckinReminderBanner;
