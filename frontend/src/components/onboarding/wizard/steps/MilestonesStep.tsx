import React, { useCallback, useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useAuth } from '../../../../hooks/useAuth';
import type { StepProps } from '../StepDefinitions';

type EventType =
  | 'graduation'
  | 'wedding'
  | 'birth'
  | 'retirement'
  | 'home_purchase'
  | 'greek_event'
  | 'other';
type RowField = 'name' | 'event_date' | 'event_type' | 'estimated_cost';
type Row = {
  id: string;
  name: string;
  event_date: string;
  event_type: EventType;
  estimated_cost: string;
};
type RowErrors = Partial<Record<RowField, string>>;

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

function newId(): string {
  return crypto.randomUUID();
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function validateRow(row: Row): RowErrors {
  const next: RowErrors = {};
  if (!row.name.trim()) next.name = 'Name is required.';
  if (row.name.trim().length > 100) next.name = 'Name must be 100 characters or fewer.';
  if (!row.event_date) next.event_date = 'Event date is required.';
  else if (row.event_date <= todayIso()) next.event_date = 'Event date must be in the future.';
  if (row.estimated_cost.trim()) {
    const cost = Number.parseFloat(row.estimated_cost);
    if (!Number.isFinite(cost) || cost < 0) next.estimated_cost = 'Estimated cost must be 0 or greater.';
  }
  return next;
}

export default function MilestonesStep({ initialData, onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [rows, setRows] = useState<Row[]>(() => {
    if (Array.isArray(initialData.events)) {
      return (initialData.events as Array<Record<string, unknown>>).map((r) => ({
        id: newId(),
        name: typeof r.name === 'string' ? r.name : '',
        event_date: typeof r.event_date === 'string' ? r.event_date : typeof r.date === 'string' ? r.date : '',
        event_type: typeof r.event_type === 'string' ? (r.event_type as EventType) : 'other',
        estimated_cost:
          typeof r.estimated_cost === 'number'
            ? String(r.estimated_cost)
            : typeof r.estimated_cost === 'string'
              ? r.estimated_cost
              : typeof r.cost === 'number'
                ? String(r.cost)
                : '',
      }));
    }
    return [];
  });
  const [errorsByRow, setErrorsByRow] = useState<Record<string, RowErrors>>({});
  const [showValidationSummary, setShowValidationSummary] = useState(false);
  const [submitBanner, setSubmitBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearValidationFeedback = useCallback(() => {
    setErrorsByRow({});
    setShowValidationSummary(false);
  }, []);

  const updateRow = useCallback(
    (id: string, patch: Partial<Row>) => {
      clearValidationFeedback();
      setRows((prev) => prev.map((x) => (x.id === id ? { ...x, ...patch } : x)));
    },
    [clearValidationFeedback]
  );

  const removeRow = useCallback(
    (id: string) => {
      clearValidationFeedback();
      setRows((prev) => prev.filter((x) => x.id !== id));
    },
    [clearValidationFeedback]
  );

  const addRow = useCallback(() => {
    clearValidationFeedback();
    setRows((prev) => [...prev, { id: newId(), name: '', event_date: '', event_type: 'other', estimated_cost: '' }]);
  }, [clearValidationFeedback]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);

    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    const nextErrors: Record<string, RowErrors> = {};
    let firstInvalid: { id: string; field: RowField } | null = null;
    for (const row of rows) {
      const errs = validateRow(row);
      nextErrors[row.id] = errs;
      if (!firstInvalid && Object.keys(errs).length) {
        const order: RowField[] = ['name', 'event_date', 'event_type', 'estimated_cost'];
        const field = order.find((f) => errs[f]);
        if (field) firstInvalid = { id: row.id, field };
      }
    }
    setErrorsByRow(nextErrors);
    if (firstInvalid) {
      setShowValidationSummary(true);
      const el = document.getElementById(`${firstInvalid.id}-${firstInvalid.field}`);
      el?.focus();
      return;
    }
    setShowValidationSummary(false);

    setIsSubmitting(true);
    try {
      const events = rows.map((row) => ({
        name: row.name.trim(),
        date: row.event_date,
        cost: row.estimated_cost.trim() ? Number.parseFloat(row.estimated_cost) : 0,
        recurring: false,
        type: row.event_type,
      }));
      await onSubmit({ events });
    } catch (err) {
      setSubmitBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Important dates</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Tell us about big life events coming up. We&apos;ll factor them into your cash forecast and warn you if your savings won&apos;t cover them.
        </p>

        {showValidationSummary && Object.values(errorsByRow).some((x) => Object.keys(x).length > 0) && (
          <div className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white" role="alert">
            Please fix the highlighted errors below before continuing.
          </div>
        )}
        {submitBanner && (
          <div className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white" role="alert">
            <button
              type="button"
              className="absolute right-2 top-2 rounded p-1 text-white hover:bg-red-700"
              aria-label="Dismiss error"
              onClick={() => setSubmitBanner(null)}
            >
              ×
            </button>
            <span className="pr-8">{submitBanner}</span>
          </div>
        )}

        {rows.length === 0 ? (
          <div className="mt-6 rounded-xl border border-dashed border-[#CBD5E1] bg-[#F8FAFC] p-6 text-center">
            <button
              type="button"
              onClick={addRow}
              className="min-h-11 rounded-lg text-sm font-medium text-[#6D28D9] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
            >
              + Add an event
            </button>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {rows.map((row, idx) => (
              <div key={row.id} className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-[#64748B]">Event {idx + 1}</p>
                  <button
                    type="button"
                    className="rounded p-2 text-[#64748B] hover:bg-red-50 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E]"
                    onClick={() => removeRow(row.id)}
                    aria-label="Remove event"
                  >
                    <Trash2 className="h-5 w-5" aria-hidden />
                  </button>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <label className={labelClass} htmlFor={`${row.id}-name`}>Event name *</label>
                    <input id={`${row.id}-name`} className={inputClass} value={row.name} onChange={(e) => updateRow(row.id, { name: e.target.value })} />
                    {errorsByRow[row.id]?.name && <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].name}</p>}
                  </div>
                  <div>
                    <label className={labelClass} htmlFor={`${row.id}-event_date`}>Date *</label>
                    <input id={`${row.id}-event_date`} className={inputClass} type="date" value={row.event_date} onChange={(e) => updateRow(row.id, { event_date: e.target.value })} />
                    {errorsByRow[row.id]?.event_date && <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].event_date}</p>}
                  </div>
                  <div>
                    <label className={labelClass} htmlFor={`${row.id}-event_type`}>Type *</label>
                    <select id={`${row.id}-event_type`} className={inputClass} value={row.event_type} onChange={(e) => updateRow(row.id, { event_type: e.target.value as EventType })}>
                      <option value="graduation">Graduation</option>
                      <option value="wedding">Wedding</option>
                      <option value="birth">Birthday</option>
                      <option value="retirement">Retirement</option>
                      <option value="home_purchase">Home Purchase</option>
                      <option value="greek_event">Fraternity/Sorority event</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="sm:col-span-2">
                    <label className={labelClass} htmlFor={`${row.id}-estimated_cost`}>Estimated cost (optional)</label>
                    <input id={`${row.id}-estimated_cost`} className={inputClass} type="number" min={0} step="0.01" value={row.estimated_cost} onChange={(e) => updateRow(row.id, { estimated_cost: e.target.value })} />
                    {errorsByRow[row.id]?.estimated_cost && <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].estimated_cost}</p>}
                  </div>
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={addRow}
              className="min-h-11 rounded-lg text-sm font-medium text-[#6D28D9] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
            >
              + Add an event
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end sm:gap-4">
        <button
          type="button"
          onClick={() => onSkip()}
          className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 sm:w-auto sm:px-4"
        >
          Skip for now
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50 sm:w-auto sm:min-w-[200px]"
        >
          {isSubmitting ? 'Saving…' : 'Save and continue'}
        </button>
      </div>
    </form>
  );
}
