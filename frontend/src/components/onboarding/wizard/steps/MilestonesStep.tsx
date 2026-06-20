import React, { useCallback, useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useAuth } from '../../../../hooks/useAuth';
import MilestonePickerModal, { type NewMilestoneEvent } from '../../../MilestonePickerModal';
import {
  BABY_CATEGORIES,
  LEGACY_FIELD_TO_CATEGORY,
  MILESTONE_META,
  type MilestoneCategory,
} from '../../../../data/milestoneCategories';
import type { StepProps } from '../StepDefinitions';

type RowField = 'name' | 'event_date' | 'estimated_cost';
type Row = {
  id: string;
  name: string;
  event_date: string;
  category?: MilestoneCategory;
  estimated_cost: string;
};
type RowErrors = Partial<Record<RowField, string>>;

function newId(): string {
  return crypto.randomUUID();
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatUsd(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

function formatDisplayDate(iso: string): string {
  const parsed = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function resolveCategory(raw: Record<string, unknown>): MilestoneCategory | undefined {
  if (typeof raw.category === 'string') {
    return raw.category as MilestoneCategory;
  }
  if (typeof raw.event_type === 'string') {
    const legacy = LEGACY_FIELD_TO_CATEGORY[raw.event_type as keyof typeof LEGACY_FIELD_TO_CATEGORY];
    if (legacy) return legacy;
  }
  if (typeof raw.type === 'string') {
    const legacy = LEGACY_FIELD_TO_CATEGORY[raw.type as keyof typeof LEGACY_FIELD_TO_CATEGORY];
    if (legacy) return legacy;
  }
  return undefined;
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

export default function MilestonesStep({
  initialData,
  onSubmit,
  onSkip,
  isSubmitting: isSkipInFlight,
}: StepProps) {
  const { getAccessToken, user } = useAuth();
  const [rows, setRows] = useState<Row[]>(() => {
    if (Array.isArray(initialData.events)) {
      return (initialData.events as Array<Record<string, unknown>>).map((r) => ({
        id: typeof r.id === 'string' ? r.id : newId(),
        name: typeof r.name === 'string' ? r.name : '',
        event_date:
          typeof r.event_date === 'string'
            ? r.event_date
            : typeof r.date === 'string'
              ? r.date
              : '',
        category: resolveCategory(r),
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
  const [pickerOpen, setPickerOpen] = useState(false);

  const clearValidationFeedback = useCallback(() => {
    setErrorsByRow({});
    setShowValidationSummary(false);
  }, []);

  const removeRow = useCallback(
    (id: string) => {
      clearValidationFeedback();
      setRows((prev) => prev.filter((x) => x.id !== id));
    },
    [clearValidationFeedback]
  );

  const handleAddEvent = useCallback(
    async (event: NewMilestoneEvent) => {
      clearValidationFeedback();
      setRows((prev) => [
        ...prev,
        {
          id: event.id,
          name: event.name,
          event_date: event.date,
          category: event.category,
          estimated_cost: event.cost != null ? String(event.cost) : '',
        },
      ]);
      setPickerOpen(false);
    },
    [clearValidationFeedback]
  );

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
        const order: RowField[] = ['name', 'event_date', 'estimated_cost'];
        const field = order.find((f) => errs[f]);
        if (field) firstInvalid = { id: row.id, field };
      }
    }
    setErrorsByRow(nextErrors);
    if (firstInvalid) {
      setShowValidationSummary(true);
      return;
    }
    setShowValidationSummary(false);

    setIsSubmitting(true);
    try {
      const events = rows.map((row) => ({
        id: row.id,
        name: row.name.trim(),
        date: row.event_date,
        cost: row.estimated_cost.trim() ? Number.parseFloat(row.estimated_cost) : 0,
        recurring: false,
        category: row.category,
        type: row.category ?? 'custom',
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

        {rows.length > 0 && (
          <ul className="mt-6 space-y-3" aria-label="Added milestones">
            {rows.map((row) => {
              const emoji = row.category ? MILESTONE_META[row.category]?.emoji ?? '📅' : '📅';
              const cost = row.estimated_cost.trim() ? Number.parseFloat(row.estimated_cost) : 0;
              return (
                <li
                  key={row.id}
                  className="flex items-center gap-3 rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center text-lg" aria-hidden>
                    {emoji}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-[#1E293B]">{row.name}</p>
                    <p className="text-sm text-[#64748B]">{formatDisplayDate(row.event_date)}</p>
                    {cost > 0 && <p className="text-sm text-[#64748B]">{formatUsd(cost)}</p>}
                  </div>
                  <button
                    type="button"
                    className="rounded p-2 text-[#64748B] hover:bg-red-50 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E]"
                    onClick={() => removeRow(row.id)}
                    aria-label="Remove event"
                  >
                    <Trash2 className="h-5 w-5" aria-hidden />
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <div className={rows.length > 0 ? 'mt-4' : 'mt-6'}>
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            className="w-full rounded-xl border-2 border-dashed border-gray-200 p-4 text-sm text-purple-600 transition-colors hover:border-purple-300 hover:bg-purple-50"
          >
            + Add a milestone
          </button>
          <p className="mt-2 text-center text-xs text-gray-400">
            Nothing coming up? Use &quot;Skip for now&quot; below — no need to add placeholder events.
          </p>
        </div>
      </div>

      <MilestonePickerModal
        isOpen={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSave={handleAddEvent}
        userId={user?.id ?? ''}
      />

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end sm:gap-4">
        <button
          type="button"
          onClick={() => onSkip()}
          disabled={isSkipInFlight}
          className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:px-4"
        >
          {isSkipInFlight ? 'Skipping…' : 'Skip for now'}
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
