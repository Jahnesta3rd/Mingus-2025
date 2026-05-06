import React, { useCallback, useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import { nextIsoDateFromDayOfMonth } from '../../scheduleUtils';
import type { StepProps } from '../StepDefinitions';

type Frequency = 'weekly' | 'biweekly' | 'semimonthly' | 'monthly';

type ExpCategory =
  | 'utilities'
  | 'subscription'
  | 'debt'
  | 'family_support'
  | 'child_support'
  | 'alimony'
  | 'caregiving'
  | 'other';

type ExpenseRowState = {
  id: string;
  label: string;
  category: ExpCategory;
  amount: string;
  frequency: Frequency;
  due_day: number;
  next_date: string;
};

type RowField = 'label' | 'category' | 'amount' | 'frequency' | 'due_day' | 'next_date';
type RowErrors = Partial<Record<RowField, string>>;

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

const FREQUENCIES: Frequency[] = ['weekly', 'biweekly', 'semimonthly', 'monthly'];

const CATEGORY_OPTIONS: { value: ExpCategory; label: string }[] = [
  { value: 'utilities', label: 'Utilities (electric, water, internet, phone)' },
  { value: 'subscription', label: 'Subscriptions (streaming, software, memberships)' },
  { value: 'debt', label: 'Debt payment (student loan, credit card, personal)' },
  { value: 'family_support', label: 'Family support' },
  { value: 'child_support', label: 'Child support' },
  { value: 'alimony', label: 'Alimony' },
  { value: 'caregiving', label: 'Caregiving (daycare, eldercare)' },
  { value: 'other', label: 'Other' },
];

const CATEGORY_SET = new Set<ExpCategory>(CATEGORY_OPTIONS.map((c) => c.value));

function newId(): string {
  return crypto.randomUUID();
}

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { error?: string; message?: string };
    return j.error || j.message || text || res.statusText;
  } catch {
    return text || res.statusText || 'Request failed';
  }
}

function todayLocalMidnight(): Date {
  const n = new Date();
  return new Date(n.getFullYear(), n.getMonth(), n.getDate());
}

function parseIsoDate(iso: string): Date | null {
  if (!iso || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null;
  const [y, m, d] = iso.split('-').map((x) => parseInt(x, 10));
  if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return null;
  const dt = new Date(y, m - 1, d);
  dt.setHours(12, 0, 0, 0);
  return dt;
}

function validateExpenseRow(row: ExpenseRowState): RowErrors {
  const errors: RowErrors = {};
  if (!row.label.trim()) {
    errors.label = 'Enter a label.';
  }
  if (!CATEGORY_SET.has(row.category)) {
    errors.category = 'Choose a category.';
  }
  const amt = parseFloat(row.amount);
  if (!Number.isFinite(amt) || amt <= 0) {
    errors.amount = 'Enter an amount greater than zero.';
  }
  if (!FREQUENCIES.includes(row.frequency)) {
    errors.frequency = 'Choose a frequency.';
  }
  const dd = row.due_day;
  if (!Number.isInteger(dd) || dd < 1 || dd > 31) {
    errors.due_day = 'Due day must be between 1 and 31.';
  }
  const nd = parseIsoDate(row.next_date);
  if (!nd) {
    errors.next_date = 'Choose a valid date.';
  } else if (nd < todayLocalMidnight()) {
    errors.next_date = 'Date must be today or later.';
  }
  return errors;
}

function normalizeMonthly(amount: number, frequency: Frequency): number {
  switch (frequency) {
    case 'weekly':
      return (amount * 52) / 12;
    case 'biweekly':
      return (amount * 26) / 12;
    case 'semimonthly':
      return amount * 2;
    case 'monthly':
    default:
      return amount;
  }
}

function buildDefaultRows(): ExpenseRowState[] {
  const now = new Date();
  // F2 design: Housing and Vehicle steps (F3) will write rent/mortgage and
  // car-payment to recurring_expenses directly. Defaults here cover OTHER
  // monthly bills only. Do NOT add Rent, Mortgage, or Car Payment defaults.
  return [
    {
      id: newId(),
      label: 'Electric',
      category: 'utilities',
      amount: '',
      frequency: 'monthly',
      due_day: 1,
      next_date: nextIsoDateFromDayOfMonth(1, now),
    },
    {
      id: newId(),
      label: 'Internet',
      category: 'utilities',
      amount: '',
      frequency: 'monthly',
      due_day: 15,
      next_date: nextIsoDateFromDayOfMonth(15, now),
    },
    {
      id: newId(),
      label: 'Phone',
      category: 'utilities',
      amount: '',
      frequency: 'monthly',
      due_day: 15,
      next_date: nextIsoDateFromDayOfMonth(15, now),
    },
    {
      id: newId(),
      label: 'Streaming / Subscriptions',
      category: 'subscription',
      amount: '',
      frequency: 'monthly',
      due_day: 1,
      next_date: nextIsoDateFromDayOfMonth(1, now),
    },
  ];
}

function hydrateRows(initialData: Record<string, unknown>): ExpenseRowState[] | null {
  const raw = initialData.rows;
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const out: ExpenseRowState[] = [];
  for (const item of raw) {
    if (!item || typeof item !== 'object') continue;
    const r = item as Record<string, unknown>;
    const cat = r.category;
    const category: ExpCategory =
      typeof cat === 'string' && CATEGORY_SET.has(cat as ExpCategory)
        ? (cat as ExpCategory)
        : 'utilities';
    const dd = r.due_day;
    const dueNum =
      typeof dd === 'number' && Number.isInteger(dd)
        ? dd
        : typeof dd === 'string'
          ? parseInt(dd, 10)
          : 1;
    out.push({
      id: newId(),
      label: typeof r.label === 'string' ? r.label : '',
      category,
      amount: typeof r.amount === 'string' ? r.amount : typeof r.amount === 'number' ? String(r.amount) : '',
      frequency:
        typeof r.frequency === 'string' && FREQUENCIES.includes(r.frequency as Frequency)
          ? (r.frequency as Frequency)
          : 'monthly',
      due_day: Number.isFinite(dueNum) ? Math.min(31, Math.max(1, dueNum)) : 1,
      next_date: typeof r.next_date === 'string' ? r.next_date : '',
    });
  }
  return out.length ? out : null;
}

export default function RecurringExpensesStep({
  initialData,
  onSubmit,
  onSkip,
}: StepProps) {
  const { getAccessToken } = useAuth();
  const [rows, setRows] = useState<ExpenseRowState[]>(() => {
    const h = hydrateRows(initialData);
    if (h) return h;
    return buildDefaultRows();
  });
  const [errorsByRow, setErrorsByRow] = useState<Record<string, RowErrors>>({});
  const [submitBanner, setSubmitBanner] = useState<string | null>(null);
  const [showValidationSummary, setShowValidationSummary] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearValidationFeedback = useCallback(() => {
    setShowValidationSummary(false);
    setErrorsByRow({});
  }, []);

  const updateRow = useCallback(
    (id: string, patch: Partial<ExpenseRowState>) => {
      clearValidationFeedback();
      setRows((prev) => prev.map((x) => (x.id === id ? { ...x, ...patch } : x)));
    },
    [clearValidationFeedback]
  );

  const removeRow = useCallback(
    (id: string) => {
      clearValidationFeedback();
      setRows((prev) => (prev.length <= 1 ? prev : prev.filter((x) => x.id !== id)));
    },
    [clearValidationFeedback]
  );

  const addRow = useCallback(() => {
    clearValidationFeedback();
    const now = new Date();
    setRows((prev) => [
      ...prev,
      {
        id: newId(),
        label: '',
        category: 'other',
        amount: '',
        frequency: 'monthly',
        due_day: 1,
        next_date: nextIsoDateFromDayOfMonth(1, now),
      },
    ]);
  }, [clearValidationFeedback]);

  const validateField = useCallback((row: ExpenseRowState, field: RowField): string | undefined => {
    const full = validateExpenseRow(row);
    return full[field];
  }, []);

  const onBlurField = useCallback(
    (row: ExpenseRowState, field: RowField) => {
      const msg = validateField(row, field);
      setErrorsByRow((prev) => ({
        ...prev,
        [row.id]: {
          ...prev[row.id],
          [field]: msg,
        },
      }));
    },
    [validateField]
  );

  const postExpense = useCallback(
    async (body: Record<string, unknown>) => {
      const res = await fetch('/api/transaction-schedule/expenses', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify(body),
      });
      if (res.status !== 201 && res.status !== 200) {
        throw new Error(await readErrorMessage(res));
      }
    },
    [getAccessToken]
  );

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);

    const nextErrors: Record<string, RowErrors> = {};
    let firstInvalid: { id: string; field: RowField } | null = null;

    for (const row of rows) {
      const eRow = validateExpenseRow(row);
      nextErrors[row.id] = eRow;
      if (Object.keys(eRow).length && !firstInvalid) {
        const order: RowField[] = ['label', 'category', 'amount', 'frequency', 'due_day', 'next_date'];
        for (const f of order) {
          if (eRow[f]) {
            firstInvalid = { id: row.id, field: f };
            break;
          }
        }
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

    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    let totalMonthly = 0;
    for (const row of rows) {
      const amt = parseFloat(row.amount);
      totalMonthly += normalizeMonthly(amt, row.frequency);
    }

    setIsSubmitting(true);
    try {
      for (const row of rows) {
        const amt = parseFloat(row.amount);
        await postExpense({
          label: row.label.trim(),
          amount: amt,
          category: row.category,
          frequency: row.frequency,
          due_day: row.due_day,
          next_date: row.next_date,
        });
      }
      await onSubmit({
        count: rows.length,
        total_monthly: Math.round(totalMonthly * 100) / 100,
      });
    } catch (err) {
      setSubmitBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const dismissBanner = () => setSubmitBanner(null);

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          Recurring Expenses
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          What other monthly bills do you pay? We&apos;ll ask about rent and car payment in later steps — don&apos;t add those here.
        </p>

        {showValidationSummary &&
          Object.values(errorsByRow).some((rowErr) => rowErr && Object.keys(rowErr).length > 0) && (
            <div
              className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white"
              role="alert"
            >
              Please fix the highlighted errors below before continuing.
            </div>
          )}

        {submitBanner && (
          <div
            className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white"
            role="alert"
          >
            <button
              type="button"
              className="absolute right-2 top-2 rounded p-1 text-white hover:bg-red-700"
              aria-label="Dismiss error"
              onClick={dismissBanner}
            >
              ×
            </button>
            <span className="pr-8">{submitBanner}</span>
          </div>
        )}

        <div className="mt-6 space-y-4">
          {rows.map((row, idx) => (
            <div key={row.id} className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-[#64748B]">Bill {idx + 1}</p>
                {rows.length > 1 && (
                  <button
                    type="button"
                    aria-label="Remove expense row"
                    className="rounded p-2 text-[#64748B] hover:bg-red-50 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E]"
                    onClick={() => removeRow(row.id)}
                  >
                    <Trash2 className="h-5 w-5" aria-hidden />
                  </button>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className={labelClass} htmlFor={`${row.id}-label`}>
                    Label
                  </label>
                  <input
                    id={`${row.id}-label`}
                    className={inputClass}
                    value={row.label}
                    onChange={(e) => updateRow(row.id, { label: e.target.value })}
                    onBlur={() => onBlurField(row, 'label')}
                  />
                  {errorsByRow[row.id]?.label && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].label}</p>
                  )}
                </div>
                <div className="sm:col-span-2">
                  <label className={labelClass} htmlFor={`${row.id}-category`}>
                    Category
                  </label>
                  <select
                    id={`${row.id}-category`}
                    className={inputClass}
                    value={row.category}
                    onChange={(e) =>
                      updateRow(row.id, { category: e.target.value as ExpCategory })
                    }
                    onBlur={() => onBlurField(row, 'category')}
                  >
                    {CATEGORY_OPTIONS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                  {errorsByRow[row.id]?.category && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].category}</p>
                  )}
                </div>
                <div>
                  <label className={labelClass} htmlFor={`${row.id}-amount`}>
                    Amount
                  </label>
                  <input
                    id={`${row.id}-amount`}
                    className={inputClass}
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="0.00"
                    value={row.amount}
                    onChange={(e) => updateRow(row.id, { amount: e.target.value })}
                    onBlur={() => onBlurField(row, 'amount')}
                  />
                  {errorsByRow[row.id]?.amount && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].amount}</p>
                  )}
                </div>
                <div>
                  <label className={labelClass} htmlFor={`${row.id}-frequency`}>
                    Frequency
                  </label>
                  <select
                    id={`${row.id}-frequency`}
                    className={inputClass}
                    value={row.frequency}
                    onChange={(e) =>
                      updateRow(row.id, { frequency: e.target.value as Frequency })
                    }
                    onBlur={() => onBlurField(row, 'frequency')}
                  >
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Every 2 Weeks</option>
                    <option value="semimonthly">Twice a Month</option>
                    <option value="monthly">Monthly</option>
                  </select>
                  {errorsByRow[row.id]?.frequency && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].frequency}</p>
                  )}
                </div>
                <div>
                  <label className={labelClass} htmlFor={`${row.id}-due_day`}>
                    Due day (1–31)
                  </label>
                  <input
                    id={`${row.id}-due_day`}
                    className={inputClass}
                    type="number"
                    min={1}
                    max={31}
                    value={row.due_day}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10);
                      updateRow(row.id, {
                        due_day: Number.isFinite(v) ? Math.min(31, Math.max(1, v)) : 1,
                      });
                    }}
                    onBlur={() => onBlurField(row, 'due_day')}
                  />
                  {errorsByRow[row.id]?.due_day && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].due_day}</p>
                  )}
                </div>
                <div className="sm:col-span-2">
                  <label className={labelClass} htmlFor={`${row.id}-next_date`}>
                    Next due date
                  </label>
                  <input
                    id={`${row.id}-next_date`}
                    className={inputClass}
                    type="date"
                    value={row.next_date}
                    onChange={(e) => updateRow(row.id, { next_date: e.target.value })}
                    onBlur={() => onBlurField(row, 'next_date')}
                  />
                  {errorsByRow[row.id]?.next_date && (
                    <p className="mt-1 text-sm text-red-600">{errorsByRow[row.id].next_date}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={addRow}
          className="mt-4 min-h-11 rounded-lg text-sm font-medium text-[#6D28D9] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          + Add another bill
        </button>
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
