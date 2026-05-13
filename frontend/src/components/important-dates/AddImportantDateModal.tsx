import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { commitModule } from '../../lib/modularOnboarding';

type EventType =
  | 'graduation'
  | 'wedding'
  | 'birth'
  | 'retirement'
  | 'home_purchase'
  | 'greek_event'
  | 'other';

type CommitEventRow = {
  name: string;
  date: string;
  cost: number;
  recurring: boolean;
  type?: string;
};

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function parseProfileCustomEvents(
  important: Record<string, unknown> | null | undefined
): CommitEventRow[] {
  if (!important || typeof important !== 'object') return [];
  const raw =
    (important as { custom_events?: unknown }).custom_events ??
    (important as { customEvents?: unknown }).customEvents;
  if (!Array.isArray(raw)) return [];
  const out: CommitEventRow[] = [];
  for (const ev of raw) {
    if (!ev || typeof ev !== 'object') continue;
    const o = ev as Record<string, unknown>;
    const name = typeof o.name === 'string' ? o.name.trim() : '';
    const date = typeof o.date === 'string' ? o.date.trim() : '';
    if (!name || !date) continue;
    const cost =
      typeof o.cost === 'number' && Number.isFinite(o.cost)
        ? o.cost
        : Number.parseFloat(String(o.cost ?? 0)) || 0;
    const recurring = Boolean(o.recurring);
    const typeRaw = o.type ?? o.event_type;
    const type =
      typeof typeRaw === 'string' && typeRaw.trim() ? typeRaw.trim() : undefined;
    const row: CommitEventRow = { name, date, cost, recurring };
    if (type) row.type = type;
    out.push(row);
  }
  return out;
}

export type AddImportantDateModalProps = {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  onSaved: () => void;
};

export default function AddImportantDateModal({
  isOpen,
  onClose,
  userId,
  onSaved,
}: AddImportantDateModalProps) {
  const { getAccessToken } = useAuth();
  const [name, setName] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');
  const [recurring, setRecurring] = useState(false);
  const [eventType, setEventType] = useState<EventType>('other');
  const [nameError, setNameError] = useState<string | null>(null);
  const [dateError, setDateError] = useState<string | null>(null);
  const [costError, setCostError] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const resetForm = useCallback(() => {
    setName('');
    setEventDate('');
    setEstimatedCost('');
    setRecurring(false);
    setEventType('other');
    setNameError(null);
    setDateError(null);
    setCostError(null);
    setBanner(null);
  }, []);

  useEffect(() => {
    if (!isOpen) resetForm();
  }, [isOpen, resetForm]);

  const validate = useCallback((): boolean => {
    setNameError(null);
    setDateError(null);
    setCostError(null);
    let ok = true;
    if (!name.trim()) {
      setNameError('Name is required.');
      ok = false;
    } else if (name.trim().length > 100) {
      setNameError('Name must be 100 characters or fewer.');
      ok = false;
    }
    if (!eventDate) {
      setDateError('Event date is required.');
      ok = false;
    } else if (eventDate <= todayIso()) {
      setDateError('Event date must be in the future.');
      ok = false;
    }
    if (estimatedCost.trim()) {
      const cost = Number.parseFloat(estimatedCost);
      if (!Number.isFinite(cost) || cost < 0) {
        setCostError('Estimated cost must be 0 or greater.');
        ok = false;
      }
    }
    return ok;
  }, [name, eventDate, estimatedCost]);

  const fetchExistingEvents = useCallback(async (): Promise<CommitEventRow[]> => {
    const token = localStorage.getItem('mingus_token');
    const response = await fetch(
      `/api/user/profile?userId=${encodeURIComponent(userId)}`,
      {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'Content-Type': 'application/json',
        },
      }
    );
    if (!response.ok) return [];
    const json: unknown = await response.json();
    const profile =
      json && typeof json === 'object' && 'profile' in json
        ? (json as { profile?: Record<string, unknown> }).profile
        : (json as Record<string, unknown> | undefined);
    const important = profile?.important_dates;
    return parseProfileCustomEvents(
      important && typeof important === 'object'
        ? (important as Record<string, unknown>)
        : undefined
    );
  }, [userId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBanner(null);
    if (!validate()) return;

    const token = getAccessToken();
    if (!token) {
      setBanner('You must be signed in to save.');
      return;
    }

    setSubmitting(true);
    try {
      const existing = await fetchExistingEvents();
      const newRow: CommitEventRow = {
        name: name.trim(),
        date: eventDate,
        cost: estimatedCost.trim() ? Number.parseFloat(estimatedCost) : 0,
        recurring,
        type: eventType,
      };
      const events = [...existing, newRow];
      const resp = await commitModule(token, 'milestones', { events });
      if (resp.failed_fields && resp.failed_fields.length > 0) {
        const summary = resp.failed_fields
          .map((f) => `${f.field_path}: ${f.reason}`)
          .join('; ');
        setBanner(`Could not save — ${summary}`);
        return;
      }
      onSaved();
      resetForm();
    } catch (err) {
      setBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-900/60 p-0 sm:items-center sm:p-4"
      role="presentation"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-[380px] flex-col rounded-t-2xl border border-[#E2E8F0] bg-white shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-important-date-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-[#E2E8F0] px-4 py-3">
          <h2 id="add-important-date-title" className="text-lg font-semibold text-[#1E293B]">
            Add important date
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-2xl leading-none text-[#64748B] hover:bg-[#F1F5F9] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E]"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form
          onSubmit={(e) => void handleSubmit(e)}
          className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4"
        >
          {banner ? (
            <div
              className="rounded-lg border border-red-700 bg-red-600 px-3 py-2 text-sm text-white"
              role="alert"
            >
              {banner}
            </div>
          ) : null}

          <div>
            <label className={labelClass} htmlFor="ida-name">
              Event name *
            </label>
            <input
              id="ida-name"
              className={inputClass}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="off"
            />
            {nameError ? (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {nameError}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClass} htmlFor="ida-date">
              Date *
            </label>
            <input
              id="ida-date"
              type="date"
              className={inputClass}
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
            />
            {dateError ? (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {dateError}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClass} htmlFor="ida-type">
              Type *
            </label>
            <select
              id="ida-type"
              className={inputClass}
              value={eventType}
              onChange={(e) => setEventType(e.target.value as EventType)}
            >
              <option value="graduation">Graduation</option>
              <option value="wedding">Wedding</option>
              <option value="birth">Birthday</option>
              <option value="retirement">Retirement</option>
              <option value="home_purchase">Home Purchase</option>
              <option value="greek_event">Fraternity/Sorority event</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className={labelClass} htmlFor="ida-cost">
              Estimated cost (optional)
            </label>
            <input
              id="ida-cost"
              type="number"
              min={0}
              step="0.01"
              className={inputClass}
              value={estimatedCost}
              onChange={(e) => setEstimatedCost(e.target.value)}
            />
            {costError ? (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {costError}
              </p>
            ) : null}
          </div>

          <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm font-medium text-[#1E293B]">
            <input
              type="checkbox"
              className="h-5 w-5 shrink-0 rounded border-[#CBD5E1] text-[#5B2D8E] focus:ring-[#5B2D8E]"
              checked={recurring}
              onChange={(e) => setRecurring(e.target.checked)}
            />
            Repeats every year
          </label>

          <div className="mt-2 flex flex-col-reverse gap-3 border-t border-[#E2E8F0] pt-4 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="min-h-11 w-full rounded-lg border border-[#E2E8F0] px-4 text-sm font-medium text-[#64748B] hover:bg-[#F8FAFC] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] sm:w-auto"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="min-h-11 w-full rounded-xl bg-[#5B2D8E] px-6 text-sm font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] disabled:opacity-50 sm:w-auto"
            >
              {submitting ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
