import React, { useCallback, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';
import {
  nextIsoDateFromDayOfMonth,
  nextIsoDateSemimonthly,
  type ScheduleFrequency,
} from './scheduleUtils';

export interface IncomeScheduleStepProps {
  onContinue: () => void;
  onSkip: () => void;
  onRefreshSetup: () => Promise<void>;
  setPageError: (msg: string | null) => void;
}

type EarnedRow = {
  id: string;
  label: string;
  amount: string;
  frequency: ScheduleFrequency;
  nextDateIso: string;
  monthDay: string;
  semiDay1: string;
  semiDay2: string;
};

interface SupportReceiveRowState {
  open: boolean;
  amount: string;
  frequency: ScheduleFrequency;
  nextDateIso: string;
  monthDay: string;
}

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

function resolveEarnedNextDate(row: EarnedRow): string | null {
  if (row.frequency === 'weekly' || row.frequency === 'biweekly') {
    if (!row.nextDateIso || !/^\d{4}-\d{2}-\d{2}$/.test(row.nextDateIso)) return null;
    return row.nextDateIso;
  }
  if (row.frequency === 'monthly') {
    const d = parseInt(row.monthDay, 10);
    if (!Number.isFinite(d) || d < 1 || d > 31) return null;
    return nextIsoDateFromDayOfMonth(d);
  }
  const d1 = parseInt(row.semiDay1, 10);
  const d2 = parseInt(row.semiDay2, 10);
  if (!Number.isFinite(d1) || !Number.isFinite(d2) || d1 < 1 || d1 > 31 || d2 < 1 || d2 > 31) {
    return null;
  }
  return nextIsoDateSemimonthly(d1, d2);
}

function resolveSupportNextDate(
  frequency: ScheduleFrequency,
  nextDateIso: string,
  monthDay: string
): string | null {
  if (frequency === 'weekly' || frequency === 'biweekly') {
    if (!nextDateIso || !/^\d{4}-\d{2}-\d{2}$/.test(nextDateIso)) return null;
    return nextDateIso;
  }
  if (frequency === 'semimonthly') {
    return null;
  }
  const d = parseInt(monthDay, 10);
  if (!Number.isFinite(d) || d < 1 || d > 31) return null;
  return nextIsoDateFromDayOfMonth(d);
}

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

export default function IncomeScheduleStep({
  onContinue,
  onSkip,
  onRefreshSetup,
  setPageError,
}: IncomeScheduleStepProps) {
  const { getAccessToken } = useAuth();
  const [earnedRows, setEarnedRows] = useState<EarnedRow[]>(() => [
    {
      id: newId(),
      label: '',
      amount: '',
      frequency: 'biweekly',
      nextDateIso: '',
      monthDay: '',
      semiDay1: '1',
      semiDay2: '15',
    },
  ]);
  const [supportSectionOpen, setSupportSectionOpen] = useState(false);
  const [childRecv, setChildRecv] = useState<SupportReceiveRowState>({
    open: false,
    amount: '',
    frequency: 'monthly',
    nextDateIso: '',
    monthDay: '',
  });
  const [alimonyRecv, setAlimonyRecv] = useState<SupportReceiveRowState>({
    open: false,
    amount: '',
    frequency: 'monthly',
    nextDateIso: '',
    monthDay: '',
  });
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const addEarned = useCallback(() => {
    setEarnedRows((r) =>
      r.length >= 3
        ? r
        : [
            ...r,
            {
              id: newId(),
              label: '',
              amount: '',
              frequency: 'biweekly',
              nextDateIso: '',
              monthDay: '',
              semiDay1: '1',
              semiDay2: '15',
            },
          ]
    );
  }, []);

  const updateEarned = useCallback((id: string, patch: Partial<EarnedRow>) => {
    setEarnedRows((rows) => rows.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  }, []);

  const postIncome = useCallback(
    async (body: Record<string, unknown>) => {
      const res = await fetch('/api/transaction-schedule/income', {
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

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPageError(null);

    const earnedPayloads: { label: string; amount: number; frequency: ScheduleFrequency; next_date: string }[] =
      [];
    for (const row of earnedRows) {
      const label = row.label.trim();
      const amt = parseFloat(row.amount);
      if (!label && (!Number.isFinite(amt) || amt <= 0)) continue;
      if (!label) {
        setPageError('Each income stream needs a label.');
        return;
      }
      if (!Number.isFinite(amt) || amt <= 0) {
        setPageError('Enter a take-home amount for each labeled stream.');
        return;
      }
      const nextDate = resolveEarnedNextDate(row);
      if (!nextDate) {
        setPageError('Choose a valid next pay date or day(s) of the month for each stream.');
        return;
      }
      earnedPayloads.push({
        label,
        amount: amt,
        frequency: row.frequency,
        next_date: nextDate,
      });
    }

    const supportPayloads: {
      label: string;
      amount: number;
      frequency: ScheduleFrequency;
      next_date: string;
      income_type: 'child_support' | 'alimony';
    }[] = [];

    if (childRecv.open) {
      const amt = parseFloat(childRecv.amount);
      if (Number.isFinite(amt) && amt > 0) {
        if (childRecv.frequency === 'semimonthly') {
          setPageError('For child support you receive, use weekly, biweekly, or monthly.');
          return;
        }
        const nd = resolveSupportNextDate(
          childRecv.frequency,
          childRecv.nextDateIso,
          childRecv.monthDay
        );
        if (!nd) {
          setPageError('Add a next payment date (or day of month) for child support you receive.');
          return;
        }
        supportPayloads.push({
          label: 'Child support I receive',
          amount: amt,
          frequency: childRecv.frequency,
          next_date: nd,
          income_type: 'child_support',
        });
      }
    }

    if (alimonyRecv.open) {
      const amt = parseFloat(alimonyRecv.amount);
      if (Number.isFinite(amt) && amt > 0) {
        if (alimonyRecv.frequency === 'semimonthly') {
          setPageError('For alimony you receive, use weekly, biweekly, or monthly.');
          return;
        }
        const nd = resolveSupportNextDate(
          alimonyRecv.frequency,
          alimonyRecv.nextDateIso,
          alimonyRecv.monthDay
        );
        if (!nd) {
          setPageError('Add a next payment date (or day of month) for alimony you receive.');
          return;
        }
        supportPayloads.push({
          label: 'Alimony I receive',
          amount: amt,
          frequency: alimonyRecv.frequency,
          next_date: nd,
          income_type: 'alimony',
        });
      }
    }

    if (earnedPayloads.length === 0 && supportPayloads.length === 0) {
      setPageError('Add at least one paycheck or support payment, or use “I’ll set this up later”.');
      return;
    }

    setSaving(true);
    try {
      for (const p of earnedPayloads) {
        await postIncome({
          label: p.label,
          amount: p.amount,
          frequency: p.frequency,
          next_date: p.next_date,
          income_type: 'earned',
        });
      }
      for (const p of supportPayloads) {
        await postIncome({
          label: p.label,
          amount: p.amount,
          frequency: p.frequency,
          next_date: p.next_date,
          income_type: p.income_type,
        });
      }
      await onRefreshSetup();
      setShowSuccess(true);
      window.setTimeout(() => {
        setShowSuccess(false);
        onContinue();
      }, 900);
    } catch (err) {
      setPageError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const freqSelect = (
    id: string,
    value: ScheduleFrequency,
    onChange: (v: ScheduleFrequency) => void
  ) => (
    <select
      id={id}
      className={inputClass}
      value={value}
      onChange={(e) => onChange(e.target.value as ScheduleFrequency)}
    >
      <option value="weekly">Weekly</option>
      <option value="biweekly">Every 2 Weeks</option>
      <option value="semimonthly">Twice a Month</option>
      <option value="monthly">Monthly</option>
    </select>
  );

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          When does money come in?
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Tell us about your income so we can map your cash flow.
        </p>

        <div className="mt-6 space-y-4">
          {earnedRows.map((row, idx) => (
            <div
              key={row.id}
              className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4"
            >
              <p className="mb-3 text-sm font-medium text-[#64748B]">Income {idx + 1}</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className={labelClass} htmlFor={`${row.id}-label`}>
                    Label
                  </label>
                  <input
                    id={`${row.id}-label`}
                    className={inputClass}
                    placeholder="e.g. Main Job, Side Hustle"
                    value={row.label}
                    onChange={(e) => updateEarned(row.id, { label: e.target.value })}
                  />
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
                    placeholder="Take-home per paycheck"
                    value={row.amount}
                    onChange={(e) => updateEarned(row.id, { amount: e.target.value })}
                  />
                </div>
                <div>
                  <label className={labelClass} htmlFor={`${row.id}-frequency`}>
                    Frequency
                  </label>
                  {freqSelect(`${row.id}-frequency`, row.frequency, (v) =>
                    updateEarned(row.id, { frequency: v })
                  )}
                </div>
                {(row.frequency === 'weekly' || row.frequency === 'biweekly') && (
                  <div className="sm:col-span-2">
                    <label className={labelClass} htmlFor={`${row.id}-next-pay`}>
                      Next pay date
                    </label>
                    <input
                      id={`${row.id}-next-pay`}
                      className={inputClass}
                      type="date"
                      value={row.nextDateIso}
                      onChange={(e) => updateEarned(row.id, { nextDateIso: e.target.value })}
                    />
                  </div>
                )}
                {row.frequency === 'monthly' && (
                  <div className="sm:col-span-2">
                    <label className={labelClass} htmlFor={`${row.id}-month-day`}>
                      Day of month you get paid
                    </label>
                    <input
                      id={`${row.id}-month-day`}
                      className={inputClass}
                      type="number"
                      min={1}
                      max={31}
                      placeholder="1–31"
                      value={row.monthDay}
                      onChange={(e) => updateEarned(row.id, { monthDay: e.target.value })}
                    />
                  </div>
                )}
                {row.frequency === 'semimonthly' && (
                  <div className="grid gap-3 sm:col-span-2 sm:grid-cols-2">
                    <div>
                      <label className={labelClass} htmlFor={`${row.id}-semi-1`}>
                        First pay day (1–31)
                      </label>
                      <input
                        id={`${row.id}-semi-1`}
                        className={inputClass}
                        type="number"
                        min={1}
                        max={31}
                        value={row.semiDay1}
                        onChange={(e) => updateEarned(row.id, { semiDay1: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelClass} htmlFor={`${row.id}-semi-2`}>
                        Second pay day (1–31)
                      </label>
                      <input
                        id={`${row.id}-semi-2`}
                        className={inputClass}
                        type="number"
                        min={1}
                        max={31}
                        value={row.semiDay2}
                        onChange={(e) => updateEarned(row.id, { semiDay2: e.target.value })}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {earnedRows.length < 3 && (
          <button
            type="button"
            onClick={addEarned}
            className="mt-4 min-h-11 rounded-lg text-sm font-medium text-[#6D28D9] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Add another income source
          </button>
        )}
      </div>

      <div className="rounded-xl border border-[#E2E8F0] bg-white shadow-sm">
        <button
          type="button"
          onClick={() => setSupportSectionOpen((o) => !o)}
          aria-expanded={supportSectionOpen}
          className="flex min-h-11 w-full items-center justify-between gap-2 px-6 py-4 text-left text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#5B2D8E]"
        >
          <span className="font-medium">Do you receive support payments regularly?</span>
          {supportSectionOpen ? (
            <ChevronDown className="h-5 w-5 shrink-0 text-[#64748B]" aria-hidden />
          ) : (
            <ChevronRight className="h-5 w-5 shrink-0 text-[#64748B]" aria-hidden />
          )}
        </button>
        {supportSectionOpen && (
          <div className="space-y-2 border-t border-[#E2E8F0] px-6 pb-6 pt-4">
            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => setChildRecv((s) => ({ ...s, open: !s.open }))}
                aria-expanded={childRecv.open}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#5B2D8E]"
              >
                Child support I receive
                {childRecv.open ? (
                  <ChevronDown className="h-4 w-4 shrink-0" aria-hidden />
                ) : (
                  <ChevronRight className="h-4 w-4 shrink-0" aria-hidden />
                )}
              </button>
              {childRecv.open && (
                <div className="grid gap-3 border-t border-[#E2E8F0] p-4 sm:grid-cols-2">
                  <div>
                    <label className={labelClass} htmlFor="income-child-amount">
                      Amount
                    </label>
                    <input
                      id="income-child-amount"
                      className={inputClass}
                      type="number"
                      min={0}
                      step="0.01"
                      value={childRecv.amount}
                      onChange={(e) => setChildRecv((s) => ({ ...s, amount: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className={labelClass} htmlFor="income-child-frequency">
                      Frequency
                    </label>
                    {freqSelect('income-child-frequency', childRecv.frequency, (v) =>
                      setChildRecv((s) => ({ ...s, frequency: v }))
                    )}
                  </div>
                  {(childRecv.frequency === 'weekly' || childRecv.frequency === 'biweekly') && (
                    <div className="sm:col-span-2">
                      <label className={labelClass} htmlFor="income-child-next">
                        Next payment date
                      </label>
                      <input
                        id="income-child-next"
                        className={inputClass}
                        type="date"
                        value={childRecv.nextDateIso}
                        onChange={(e) => setChildRecv((s) => ({ ...s, nextDateIso: e.target.value }))}
                      />
                    </div>
                  )}
                  {childRecv.frequency === 'monthly' && (
                    <div className="sm:col-span-2">
                      <label className={labelClass} htmlFor="income-child-month-day">
                        Day of month
                      </label>
                      <input
                        id="income-child-month-day"
                        className={inputClass}
                        type="number"
                        min={1}
                        max={31}
                        value={childRecv.monthDay}
                        onChange={(e) => setChildRecv((s) => ({ ...s, monthDay: e.target.value }))}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => setAlimonyRecv((s) => ({ ...s, open: !s.open }))}
                aria-expanded={alimonyRecv.open}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#5B2D8E]"
              >
                Alimony I receive
                {alimonyRecv.open ? (
                  <ChevronDown className="h-4 w-4 shrink-0" aria-hidden />
                ) : (
                  <ChevronRight className="h-4 w-4 shrink-0" aria-hidden />
                )}
              </button>
              {alimonyRecv.open && (
                <div className="grid gap-3 border-t border-[#E2E8F0] p-4 sm:grid-cols-2">
                  <div>
                    <label className={labelClass} htmlFor="income-alimony-amount">
                      Amount
                    </label>
                    <input
                      id="income-alimony-amount"
                      className={inputClass}
                      type="number"
                      min={0}
                      step="0.01"
                      value={alimonyRecv.amount}
                      onChange={(e) => setAlimonyRecv((s) => ({ ...s, amount: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className={labelClass} htmlFor="income-alimony-frequency">
                      Frequency
                    </label>
                    {freqSelect('income-alimony-frequency', alimonyRecv.frequency, (v) =>
                      setAlimonyRecv((s) => ({ ...s, frequency: v }))
                    )}
                  </div>
                  {(alimonyRecv.frequency === 'weekly' || alimonyRecv.frequency === 'biweekly') && (
                    <div className="sm:col-span-2">
                      <label className={labelClass} htmlFor="income-alimony-next">
                        Next payment date
                      </label>
                      <input
                        id="income-alimony-next"
                        className={inputClass}
                        type="date"
                        value={alimonyRecv.nextDateIso}
                        onChange={(e) => setAlimonyRecv((s) => ({ ...s, nextDateIso: e.target.value }))}
                      />
                    </div>
                  )}
                  {alimonyRecv.frequency === 'monthly' && (
                    <div className="sm:col-span-2">
                      <label className={labelClass} htmlFor="income-alimony-month-day">
                        Day of month
                      </label>
                      <input
                        id="income-alimony-month-day"
                        className={inputClass}
                        type="number"
                        min={1}
                        max={31}
                        value={alimonyRecv.monthDay}
                        onChange={(e) => setAlimonyRecv((s) => ({ ...s, monthDay: e.target.value }))}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {showSuccess && (
        <div
          className="rounded-lg border border-[#059669]/30 bg-emerald-50 px-4 py-3 text-sm text-[#059669]"
          role="status"
        >
          Saved. Continuing…
        </div>
      )}

      <button
        type="submit"
        disabled={saving}
        className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save & Continue'}
      </button>

      <button
        type="button"
        onClick={() => {
          setPageError(null);
          onSkip();
        }}
        className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
      >
        I&apos;ll set this up later
      </button>
    </form>
  );
}
