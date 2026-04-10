import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

const US_TIMEZONES = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Phoenix',
  'America/Los_Angeles',
  'America/Anchorage',
  'Pacific/Honolulu',
  'America/Puerto_Rico',
] as const;

const DAY_DEFS: { key: string; label: string }[] = [
  { key: 'mon', label: 'Mon' },
  { key: 'tue', label: 'Tue' },
  { key: 'wed', label: 'Wed' },
  { key: 'thu', label: 'Thu' },
  { key: 'fri', label: 'Fri' },
  { key: 'sat', label: 'Sat' },
  { key: 'sun', label: 'Sun' },
];

export interface SpiritPrefsApi {
  reminders_enabled: boolean;
  reminder_hour: number;
  reminder_timezone: string;
  reminder_days: string;
  streak_nudge_enabled: boolean;
  last_reminder_sent?: string | null;
  updated_at?: string | null;
}

function buildHeaders(getAccessToken: () => string | null, json = false): HeadersInit {
  const h: Record<string, string> = {
    ...csrfHeaders(),
  };
  if (json) {
    h['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

function parseReminderDays(s: string): Set<string> {
  return new Set(
    s
      .split(',')
      .map((x) => x.trim().toLowerCase())
      .filter(Boolean)
  );
}

const HOUR_LABELS = Array.from({ length: 24 }, (_, h) => {
  const period = h >= 12 ? 'PM' : 'AM';
  const hr12 = h % 12 === 0 ? 12 : h % 12;
  return { value: h, label: `${hr12} ${period}` };
});

const NotificationPrefsForm: React.FC = () => {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [remindersEnabled, setRemindersEnabled] = useState(true);
  const [reminderHour, setReminderHour] = useState(8);
  const [reminderTimezone, setReminderTimezone] = useState('America/New_York');
  const [daySet, setDaySet] = useState<Set<string>>(() => parseReminderDays('mon,tue,wed,thu,fri,sat,sun'));
  const [streakNudge, setStreakNudge] = useState(true);

  const reminderDaysString = useMemo(() => {
    return DAY_DEFS.map((d) => d.key).filter((k) => daySet.has(k)).join(',');
  }, [daySet]);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/spirit/prefs', {
        method: 'GET',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error((j as { error?: string }).error || res.statusText);
      }
      const data = (await res.json()) as SpiritPrefsApi;
      setRemindersEnabled(!!data.reminders_enabled);
      setReminderHour(typeof data.reminder_hour === 'number' ? data.reminder_hour : 8);
      setReminderTimezone(data.reminder_timezone || 'America/New_York');
      setDaySet(parseReminderDays(data.reminder_days || 'mon,tue,wed,thu,fri,sat,sun'));
      setStreakNudge(data.streak_nudge_enabled !== false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load preferences');
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, isAuthenticated]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(t);
  }, [toast]);

  const toggleDay = (key: string) => {
    setDaySet((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const save = async () => {
    if (!isAuthenticated) return;
    if (!reminderDaysString) {
      setError('Select at least one day for reminders.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/spirit/prefs', {
        method: 'PUT',
        credentials: 'include',
        headers: buildHeaders(getAccessToken, true),
        body: JSON.stringify({
          reminders_enabled: remindersEnabled,
          reminder_hour: reminderHour,
          reminder_timezone: reminderTimezone,
          reminder_days: reminderDaysString,
          streak_nudge_enabled: streakNudge,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error((j as { error?: string }).error || res.statusText);
      }
      setToast('Practice reminder settings saved.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <p className="text-sm text-gray-600">
        Sign in to manage Spirit &amp; Finance practice reminders.
      </p>
    );
  }

  if (loading) {
    return <p className="text-sm text-gray-500">Loading reminder settings…</p>;
  }

  return (
    <div id="practice-reminders" className="space-y-6">
      {toast ? (
        <div
          className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
          role="status"
        >
          {toast}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      ) : null}

      <label className="flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div>
          <div className="font-medium text-gray-900">Enable daily reminders</div>
          <div className="text-sm text-gray-500">Email + in-app nudge at your chosen time</div>
        </div>
        <input
          type="checkbox"
          className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          checked={remindersEnabled}
          onChange={(e) => setRemindersEnabled(e.target.checked)}
        />
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="spirit-reminder-hour" className="mb-1 block text-sm font-medium text-gray-700">
            Reminder time
          </label>
          <select
            id="spirit-reminder-hour"
            className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={reminderHour}
            onChange={(e) => setReminderHour(Number(e.target.value))}
          >
            {HOUR_LABELS.map((h) => (
              <option key={h.value} value={h.value}>
                {h.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="spirit-reminder-tz" className="mb-1 block text-sm font-medium text-gray-700">
            Timezone
          </label>
          <select
            id="spirit-reminder-tz"
            className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={reminderTimezone}
            onChange={(e) => setReminderTimezone(e.target.value)}
          >
            {US_TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>
                {tz.replace('America/', '').replace('Pacific/', 'Pacific — ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <div className="mb-2 text-sm font-medium text-gray-700">Reminder days</div>
        <div className="flex flex-wrap gap-2">
          {DAY_DEFS.map(({ key, label }) => (
            <label
              key={key}
              className={`inline-flex cursor-pointer items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                daySet.has(key)
                  ? 'border-blue-600 bg-blue-50 text-blue-800'
                  : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={daySet.has(key)}
                onChange={() => toggleDay(key)}
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <label className="flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div>
          <div className="font-medium text-gray-900">Streak risk nudge</div>
          <div className="text-sm text-gray-500">Extra encouragement when your streak could break</div>
        </div>
        <input
          type="checkbox"
          className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          checked={streakNudge}
          onChange={(e) => setStreakNudge(e.target.checked)}
        />
      </label>

      <button
        type="button"
        onClick={() => void save()}
        disabled={saving}
        className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save practice reminders'}
      </button>
    </div>
  );
};

export default NotificationPrefsForm;
