import React, { useState, useEffect, useCallback } from 'react';

// ========================================
// TYPES (API shape: important_dates)
// ========================================

interface DatedCost {
  date: string;
  cost: number;
}

interface CustomEvent {
  name: string;
  date: string;
  cost: number;
}

interface ImportantDatesData {
  birthday: string | null;
  vacation: DatedCost | null;
  car_inspection: DatedCost | null;
  sisters_wedding: DatedCost | null;
  custom_events?: CustomEvent[];
}

interface ProfileResponse {
  profile: {
    important_dates: ImportantDatesData | null;
    [key: string]: unknown;
  };
}

interface SpecialDatesWidgetProps {
  userId: string;
  userEmail: string;
  className?: string;
  /** Callback to open the Financial Forecast tab (e.g. from dashboard). Used for shortfall "Review forecast" link. */
  onNavigateToForecast?: () => void;
}

/** Shape from GET /api/cash-flow/backward-compatibility/{userEmail} forecast.daily_cashflow */
interface DailyCashflow {
  date: string;
  closing_balance: number;
}

interface NormalizedEvent {
  name: string;
  date: string; // ISO date for sorting/display
  cost: number;
  emoji: string;
}

// ========================================
// HELPERS
// ========================================

const EVENT_EMOJI: Record<string, string> = {
  birthday: '🎂',
  vacation: '✈️',
  car_inspection: '🚗',
  sisters_wedding: '💍',
  custom: '📅',
};

function formatLabel(key: string): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

/** Get next calendar occurrence of a birthday (YYYY-MM-DD). Exported for tests. */
export function getNextBirthdayDate(birthdayIso: string): string {
  const [y, m, d] = birthdayIso.split('-').map(Number);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let next = new Date(today.getFullYear(), m - 1, d);
  if (next < today) {
    next = new Date(today.getFullYear() + 1, m - 1, d);
  }
  return next.toISOString().slice(0, 10);
}

function daysBetween(from: Date, to: Date): number {
  const a = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  const b = new Date(to.getFullYear(), to.getMonth(), to.getDate());
  return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24));
}

/** Exported for tests. */
export function getCountdownBadge(eventDate: string): { label: string; className: string } {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(eventDate + 'T00:00:00');
  const days = daysBetween(today, target);

  if (days <= 7) {
    return { label: days === 0 ? 'Today' : `${days} day${days === 1 ? '' : 's'}`, className: 'bg-red-100 text-red-800' };
  }
  if (days <= 30) {
    return { label: `${days} days`, className: 'bg-amber-100 text-amber-800' };
  }
  if (days <= 90) {
    return { label: `${days} days`, className: 'bg-blue-100 text-blue-800' };
  }
  const months = Math.round(days / 30);
  return { label: `in ${months} month${months === 1 ? '' : 's'}`, className: 'bg-gray-100 text-gray-700' };
}

function normalizeEvents(data: ImportantDatesData | null): NormalizedEvent[] {
  if (!data) return [];

  const today = new Date().toISOString().slice(0, 10);
  const out: NormalizedEvent[] = [];

  if (data.birthday) {
    const nextDate = getNextBirthdayDate(data.birthday);
    if (nextDate >= today) {
      out.push({
        name: 'Birthday',
        date: nextDate,
        cost: 0,
        emoji: EVENT_EMOJI.birthday,
      });
    }
  }

  if (data.vacation?.date && data.vacation.date >= today) {
    out.push({
      name: formatLabel('vacation'),
      date: data.vacation.date,
      cost: data.vacation.cost,
      emoji: EVENT_EMOJI.vacation,
    });
  }
  if (data.car_inspection?.date && data.car_inspection.date >= today) {
    out.push({
      name: formatLabel('car_inspection'),
      date: data.car_inspection.date,
      cost: data.car_inspection.cost,
      emoji: EVENT_EMOJI.car_inspection,
    });
  }
  if (data.sisters_wedding?.date && data.sisters_wedding.date >= today) {
    out.push({
      name: formatLabel('sisters_wedding'),
      date: data.sisters_wedding.date,
      cost: data.sisters_wedding.cost,
      emoji: EVENT_EMOJI.sisters_wedding,
    });
  }

  const custom = data.custom_events ?? [];
  custom.forEach((ev) => {
    if (ev.date >= today) {
      out.push({
        name: ev.name.charAt(0).toUpperCase() + ev.name.slice(1),
        date: ev.date,
        cost: ev.cost,
        emoji: EVENT_EMOJI.custom,
      });
    }
  });

  out.sort((a, b) => a.date.localeCompare(b.date));
  return out;
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
}

const IconCovered = () => (
  <svg className="h-4 w-4 text-green-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
  </svg>
);
const IconTight = () => (
  <svg className="h-4 w-4 text-amber-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
    <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
  </svg>
);
const IconShortfall = () => (
  <svg className="h-4 w-4 text-red-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
  </svg>
);

// ========================================
// MAIN COMPONENT
// ========================================

export default function SpecialDatesWidget({
  userId,
  userEmail,
  className = '',
  onNavigateToForecast,
}: SpecialDatesWidgetProps) {
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cashflow, setCashflow] = useState<DailyCashflow[]>([]);
  const [cashflowLoading, setCashflowLoading] = useState(true);
  const [tooltipIndex, setTooltipIndex] = useState<number | null>(null);

  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('mingus_token');
      const response = await fetch(
        `/api/user/profile?userId=${encodeURIComponent(userId)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      if (!response.ok) throw new Error('Failed to load profile');
      const json: ProfileResponse = await response.json();
      setProfile(json);
    } catch {
      setError('Unable to load events. Tap to retry.');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    if (!userEmail) {
      setCashflowLoading(false);
      return;
    }
    let cancelled = false;
    setCashflowLoading(true);
    const token = localStorage.getItem('mingus_token');
    fetch(`/api/cash-flow/backward-compatibility/${encodeURIComponent(userEmail)}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('Failed to load'))))
      .then((data: { forecast?: { daily_cashflow?: DailyCashflow[] } }) => {
        if (!cancelled) {
          setCashflow(data?.forecast?.daily_cashflow ?? []);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCashflow([]);
        }
      })
      .finally(() => {
        if (!cancelled) setCashflowLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userEmail]);

  const getForecastImpact = useCallback(
    (eventDate: Date, eventCost: number): 'covered' | 'tight' | 'shortfall' | null => {
      if (!cashflow.length || eventCost === 0) return null;
      const dateStr = eventDate.toISOString().split('T')[0];
      const dayData = cashflow.find((d) => d.date === dateStr);
      if (!dayData) return null;
      const afterEvent = dayData.closing_balance - eventCost;
      if (afterEvent > 500) return 'covered';
      if (afterEvent >= 0) return 'tight';
      return 'shortfall';
    },
    [cashflow]
  );

  const importantDates = profile?.profile?.important_dates ?? null;
  const events = normalizeEvents(importantDates);
  const isEmpty = events.length === 0 && !loading && !error;

  const profileLink = '/profile#important-dates';

  // Loading: skeleton
  if (loading) {
    return (
      <div
        className={`rounded-xl bg-white p-6 shadow-sm ${className}`}
        role="status"
        aria-label="Loading events"
      >
        <div className="mb-4 h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="max-h-[320px] space-y-0 overflow-hidden">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 border-b border-gray-100 py-3 last:border-0">
              <div className="h-8 w-8 animate-pulse rounded-full bg-gray-200" />
              <div className="flex-1 space-y-1">
                <div className="h-4 w-28 animate-pulse rounded bg-gray-200" />
                <div className="h-3 w-16 animate-pulse rounded bg-gray-100" />
              </div>
              <div className="h-6 w-14 animate-pulse rounded-full bg-gray-200" />
            </div>
          ))}
        </div>
        <div className="mt-4 h-4 w-48 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  // Error: whole card clickable retry
  if (error) {
    return (
      <button
        type="button"
        onClick={fetchProfile}
        className={`block w-full rounded-xl bg-white p-6 text-left shadow-sm transition-opacity hover:opacity-90 ${className}`}
      >
        <p className="text-gray-700">{error}</p>
      </button>
    );
  }

  // Empty state
  if (isEmpty) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
        <h2 className="mb-2 text-lg font-semibold text-gray-900">Upcoming Events & Costs</h2>
        <p className="mb-4 text-gray-600">Add your upcoming events to see how they affect your finances.</p>
        <a
          href={profileLink}
          className="inline-block rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800"
        >
          Add Events
        </a>
        <p className="mt-4">
          <a href={profileLink} className="text-sm text-gray-500 underline hover:text-gray-700">
            Edit events in your profile →
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`} role="region" aria-label="Upcoming events and costs">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">Upcoming Events & Costs</h2>
      <ul className="max-h-[320px] list-none space-y-0 overflow-y-auto py-0" aria-label="Events list">
        {events.map((ev, index) => {
          const badge = getCountdownBadge(ev.date);
          const impact = ev.cost > 0 ? getForecastImpact(new Date(ev.date + 'T00:00:00'), ev.cost) : null;
          const showImpact = !cashflowLoading && impact != null;
          return (
            <li
              key={`${ev.name}-${ev.date}-${index}`}
              className="flex items-center gap-3 border-b border-gray-100 py-3 last:border-b-0"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center text-lg" aria-hidden>
                {ev.emoji}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-900">{ev.name}</p>
                {ev.cost > 0 && (
                  <p className="text-sm text-gray-500">{formatUsd(ev.cost)}</p>
                )}
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${badge.className}`}
              >
                {badge.label}
              </span>
              <div className="relative flex h-6 w-6 shrink-0 items-center justify-center">
                {cashflowLoading && ev.cost > 0 && (
                  <span
                    className="h-2 w-2 rounded-full bg-gray-400 animate-pulse"
                    aria-hidden
                  />
                )}
                {showImpact && (
                  <span
                    className="flex cursor-help items-center justify-center"
                    onMouseEnter={() => setTooltipIndex(index)}
                    onMouseLeave={() => setTooltipIndex(null)}
                    onFocus={() => setTooltipIndex(index)}
                    onBlur={() => setTooltipIndex(null)}
                    onClick={() => setTooltipIndex((i) => (i === index ? null : index))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setTooltipIndex((i) => (i === index ? null : index));
                      }
                      if (e.key === 'Escape') setTooltipIndex(null);
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label={
                      impact === 'covered'
                        ? 'Covered — your projected balance covers this cost'
                        : impact === 'tight'
                          ? 'Tight — you will have just enough based on your current forecast'
                          : 'Shortfall — based on your current forecast, you may not cover this cost. Tap to review your forecast.'
                    }
                  >
                    {impact === 'covered' && <IconCovered />}
                    {impact === 'tight' && <IconTight />}
                    {impact === 'shortfall' && <IconShortfall />}
                    {tooltipIndex === index && (
                      <span
                        className="absolute right-0 top-full z-10 mt-1 min-w-[200px] max-w-[280px] rounded-lg bg-gray-900 px-3 py-2 text-left text-xs font-medium text-white shadow-lg"
                        role="tooltip"
                      >
                        {impact === 'covered' && 'Covered — your projected balance covers this cost'}
                        {impact === 'tight' && 'Tight — you will have just enough based on your current forecast'}
                        {impact === 'shortfall' && (
                          <span>
                            Shortfall — based on your current forecast, you may not cover this cost.{' '}
                            {onNavigateToForecast ? (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setTooltipIndex(null);
                                  onNavigateToForecast();
                                }}
                                className="mt-1 block w-full rounded bg-white/20 py-1 text-center font-medium hover:bg-white/30"
                              >
                                Review your forecast
                              </button>
                            ) : (
                              <a
                                href="/dashboard#financial-forecast"
                                className="mt-1 block rounded bg-white/20 py-1 text-center font-medium hover:bg-white/30"
                                onClick={() => setTooltipIndex(null)}
                              >
                                Review your forecast
                              </a>
                            )}
                          </span>
                        )}
                      </span>
                    )}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <p className="mt-4 border-t border-gray-100 pt-4">
        <a href={profileLink} className="text-sm text-gray-500 underline hover:text-gray-700">
          Edit events in your profile →
        </a>
      </p>
    </div>
  );
}
