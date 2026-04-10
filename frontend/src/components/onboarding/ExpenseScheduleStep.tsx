import React, { useCallback, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';
import { nextIsoDateFromDayOfMonth, nextIsoDateSemimonthly, type ScheduleFrequency } from './scheduleUtils';

export interface ExpenseScheduleStepProps {
  onContinue: () => void;
  onSkip: () => void;
  onRefreshSetup: () => Promise<void>;
  setPageError: (msg: string | null) => void;
}

type ExpenseCategoryUi = 'housing' | 'transportation' | 'debt' | 'utilities' | 'subscription' | 'other';

type BillRow = {
  id: string;
  label: string;
  amount: string;
  category: ExpenseCategoryUi;
  dueDay: string;
};

type FamKey = 'child_pay' | 'alimony_pay' | 'family_send' | 'caregiving';

type FamRowState = {
  open: boolean;
  amount: string;
  dueDay: string;
  semiDay2: string;
  frequency: ScheduleFrequency;
  nextDateIso: string;
  label: string;
};

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

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

const CATEGORY_OPTIONS: { value: ExpenseCategoryUi; label: string }[] = [
  { value: 'housing', label: 'Housing' },
  { value: 'transportation', label: 'Transportation' },
  { value: 'debt', label: 'Debt' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'subscription', label: 'Subscription' },
  { value: 'other', label: 'Other' },
];

const defaultBills = (): BillRow[] => [
  { id: newId(), label: 'Rent / Mortgage', category: 'housing', amount: '', dueDay: '1' },
  { id: newId(), label: 'Car Payment', category: 'transportation', amount: '', dueDay: '1' },
  { id: newId(), label: 'Student Loan', category: 'debt', amount: '', dueDay: '1' },
];

const defaultFam = (): Record<FamKey, FamRowState> => ({
  child_pay: { open: false, amount: '', dueDay: '1', semiDay2: '15', frequency: 'monthly', nextDateIso: '', label: '' },
  alimony_pay: { open: false, amount: '', dueDay: '1', semiDay2: '15', frequency: 'monthly', nextDateIso: '', label: '' },
  family_send: {
    open: false,
    amount: '',
    dueDay: '1',
    semiDay2: '15',
    frequency: 'monthly',
    nextDateIso: '',
    label: 'Money I send to family',
  },
  caregiving: {
    open: false,
    amount: '',
    dueDay: '1',
    semiDay2: '15',
    frequency: 'monthly',
    nextDateIso: '',
    label: 'Caregiving costs',
  },
});

function buildFamPayload(
  state: FamRowState,
  category: string,
  fixedLabel: string,
  editableLabel: boolean
): { label: string; amount: number; category: string; frequency: ScheduleFrequency; due_day: number; next_date: string } | null {
  if (!state.open) return null;
  const amt = parseFloat(state.amount);
  if (!Number.isFinite(amt) || amt <= 0) return null;

  const label = editableLabel ? state.label.trim() || fixedLabel : fixedLabel;

  if (state.frequency === 'weekly' || state.frequency === 'biweekly') {
    if (!state.nextDateIso || !/^\d{4}-\d{2}-\d{2}$/.test(state.nextDateIso)) {
      throw new Error(`Choose a next payment date for “${fixedLabel}”.`);
    }
    const due = new Date(state.nextDateIso + 'T12:00:00').getDate();
    return {
      label,
      amount: amt,
      category,
      frequency: state.frequency,
      due_day: Math.min(31, Math.max(1, due)),
      next_date: state.nextDateIso,
    };
  }

  const d1 = parseInt(state.dueDay, 10);
  if (!Number.isFinite(d1) || d1 < 1 || d1 > 31) {
    throw new Error(`Due day must be 1–31 for “${fixedLabel}”.`);
  }

  if (state.frequency === 'monthly') {
    return {
      label,
      amount: amt,
      category,
      frequency: 'monthly',
      due_day: d1,
      next_date: nextIsoDateFromDayOfMonth(d1),
    };
  }

  const d2 = parseInt(state.semiDay2, 10);
  if (!Number.isFinite(d2) || d2 < 1 || d2 > 31) {
    throw new Error(`Enter two valid days of the month for “${fixedLabel}”.`);
  }
  return {
    label,
    amount: amt,
    category,
    frequency: 'semimonthly',
    due_day: d1,
    next_date: nextIsoDateSemimonthly(d1, d2),
  };
}

export default function ExpenseScheduleStep({
  onContinue,
  onSkip,
  onRefreshSetup,
  setPageError,
}: ExpenseScheduleStepProps) {
  const { getAccessToken } = useAuth();
  const [bills, setBills] = useState<BillRow[]>(defaultBills);
  const [familySectionOpen, setFamilySectionOpen] = useState(false);
  const [fam, setFam] = useState<Record<FamKey, FamRowState>>(defaultFam);
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const addBill = useCallback(() => {
    setBills((rows) =>
      rows.length >= 8
        ? rows
        : [
            ...rows,
            {
              id: newId(),
              label: '',
              amount: '',
              category: 'other',
              dueDay: '1',
            },
          ]
    );
  }, []);

  const updateBill = useCallback((id: string, patch: Partial<BillRow>) => {
    setBills((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  }, []);

  const updateFam = useCallback((key: FamKey, patch: Partial<FamRowState>) => {
    setFam((f) => ({ ...f, [key]: { ...f[key], ...patch } }));
  }, []);

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

  const freqSelect = (value: ScheduleFrequency, onChange: (v: ScheduleFrequency) => void) => (
    <select
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

  const renderFamFields = (key: FamKey, editableLabel: boolean) => {
    const s = fam[key];
    const monthlyOnly = key === 'child_pay' || key === 'alimony_pay';
    return (
      <div className="grid gap-3 border-t border-[#E2E8F0] p-4 sm:grid-cols-2">
        {editableLabel && (
          <div className="sm:col-span-2">
            <label className={labelClass}>Label</label>
            <input
              className={inputClass}
              value={s.label}
              onChange={(e) => updateFam(key, { label: e.target.value })}
            />
          </div>
        )}
        {monthlyOnly ? (
          <>
            <div>
              <label className={labelClass}>Amount</label>
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={s.amount}
                onChange={(e) => updateFam(key, { amount: e.target.value })}
              />
            </div>
            <div>
              <label className={labelClass}>Due day (1–31)</label>
              <input
                className={inputClass}
                type="number"
                min={1}
                max={31}
                value={s.dueDay}
                onChange={(e) => updateFam(key, { dueDay: e.target.value })}
              />
            </div>
          </>
        ) : (
          <>
            <div>
              <label className={labelClass}>Amount</label>
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={s.amount}
                onChange={(e) => updateFam(key, { amount: e.target.value })}
              />
            </div>
            <div>
              <label className={labelClass}>Frequency</label>
              {freqSelect(s.frequency, (v) => updateFam(key, { frequency: v }))}
            </div>
          </>
        )}
        {!monthlyOnly && (s.frequency === 'weekly' || s.frequency === 'biweekly') && (
          <div className="sm:col-span-2">
            <label className={labelClass}>Next payment date</label>
            <input
              className={inputClass}
              type="date"
              value={s.nextDateIso}
              onChange={(e) => updateFam(key, { nextDateIso: e.target.value })}
            />
          </div>
        )}
        {!monthlyOnly && s.frequency === 'monthly' && (
          <div className="sm:col-span-2">
            <label className={labelClass}>Due day (1–31)</label>
            <input
              className={inputClass}
              type="number"
              min={1}
              max={31}
              value={s.dueDay}
              onChange={(e) => updateFam(key, { dueDay: e.target.value })}
            />
          </div>
        )}
        {!monthlyOnly && s.frequency === 'semimonthly' && (
          <div className="grid gap-3 sm:col-span-2 sm:grid-cols-2">
            <div>
              <label className={labelClass}>First due day (1–31)</label>
              <input
                className={inputClass}
                type="number"
                min={1}
                max={31}
                value={s.dueDay}
                onChange={(e) => updateFam(key, { dueDay: e.target.value })}
              />
            </div>
            <div>
              <label className={labelClass}>Second due day (1–31)</label>
              <input
                className={inputClass}
                type="number"
                min={1}
                max={31}
                value={s.semiDay2}
                onChange={(e) => updateFam(key, { semiDay2: e.target.value })}
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPageError(null);

    type Payload = {
      label: string;
      amount: number;
      category: string;
      frequency: ScheduleFrequency;
      due_day: number;
      next_date: string;
    };

    const payloads: Payload[] = [];

    for (const row of bills) {
      const amt = parseFloat(row.amount);
      if (!Number.isFinite(amt) || amt <= 0) continue;
      const label = row.label.trim() || 'Bill';
      const due = parseInt(row.dueDay, 10);
      if (!Number.isFinite(due) || due < 1 || due > 31) {
        setPageError('Each bill with an amount needs a due day between 1 and 31.');
        return;
      }
      payloads.push({
        label,
        amount: amt,
        category: row.category,
        frequency: 'monthly',
        due_day: due,
        next_date: nextIsoDateFromDayOfMonth(due),
      });
    }

    try {
      const cp = buildFamPayload(fam.child_pay, 'child_support', 'Child support I pay', false);
      if (cp) payloads.push(cp);

      const ap = buildFamPayload(fam.alimony_pay, 'alimony', 'Alimony I pay', false);
      if (ap) payloads.push(ap);

      const fs = buildFamPayload(
        fam.family_send,
        'family_support',
        'Money I send to family',
        true
      );
      if (fs) payloads.push(fs);

      const cg = buildFamPayload(fam.caregiving, 'caregiving', 'Caregiving costs', true);
      if (cg) payloads.push(cg);
    } catch (err) {
      setPageError(err instanceof Error ? err.message : 'Check family obligation fields.');
      return;
    }

    if (payloads.length === 0) {
      setPageError('Add at least one bill with an amount, or use “I’ll set this up later”.');
      return;
    }

    setSaving(true);
    try {
      for (const p of payloads) {
        await postExpense({
          label: p.label,
          amount: p.amount,
          category: p.category,
          frequency: p.frequency,
          due_day: p.due_day,
          next_date: p.next_date,
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

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          What goes out every month?
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add your regular bills so we know when your balance will dip.
        </p>

        <div className="mt-6 space-y-4">
          {bills.map((row) => (
            <div key={row.id} className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className={labelClass}>Label</label>
                  <input
                    className={inputClass}
                    value={row.label}
                    onChange={(e) => updateBill(row.id, { label: e.target.value })}
                  />
                </div>
                <div>
                  <label className={labelClass}>Amount</label>
                  <input
                    className={inputClass}
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="0.00"
                    value={row.amount}
                    onChange={(e) => updateBill(row.id, { amount: e.target.value })}
                  />
                </div>
                <div>
                  <label className={labelClass}>Category</label>
                  <select
                    className={inputClass}
                    value={row.category}
                    onChange={(e) =>
                      updateBill(row.id, { category: e.target.value as ExpenseCategoryUi })
                    }
                  >
                    {CATEGORY_OPTIONS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className={labelClass}>Due day of month (1–31)</label>
                  <input
                    className={inputClass}
                    type="number"
                    min={1}
                    max={31}
                    value={row.dueDay}
                    onChange={(e) => updateBill(row.id, { dueDay: e.target.value })}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {bills.length < 8 && (
          <button
            type="button"
            onClick={addBill}
            className="mt-4 min-h-11 text-sm font-medium text-[#6D28D9] hover:underline"
          >
            Add another bill
          </button>
        )}
      </div>

      <div className="rounded-xl border border-[#E2E8F0] bg-white shadow-sm">
        <button
          type="button"
          onClick={() => setFamilySectionOpen((o) => !o)}
          className="flex min-h-11 w-full flex-col items-stretch gap-1 px-6 py-4 text-left"
        >
          <span className="flex w-full items-center justify-between gap-2 text-[#1E293B]">
            <span className="font-medium">Do you have any family or legal financial obligations?</span>
            {familySectionOpen ? (
              <ChevronDown className="h-5 w-5 shrink-0 text-[#64748B]" />
            ) : (
              <ChevronRight className="h-5 w-5 shrink-0 text-[#64748B]" />
            )}
          </span>
          <span className="text-sm text-[#64748B]">
            These are just as important as your rent — they belong in your forecast too.
          </span>
        </button>
        {familySectionOpen && (
          <div className="space-y-2 border-t border-[#E2E8F0] px-6 pb-6 pt-4">
            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => updateFam('child_pay', { open: !fam.child_pay.open })}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B]"
              >
                Child support I pay
                {fam.child_pay.open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              {fam.child_pay.open && renderFamFields('child_pay', false)}
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => updateFam('alimony_pay', { open: !fam.alimony_pay.open })}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B]"
              >
                Alimony I pay
                {fam.alimony_pay.open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              {fam.alimony_pay.open && renderFamFields('alimony_pay', false)}
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => updateFam('family_send', { open: !fam.family_send.open })}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B]"
              >
                Money I send to family
                {fam.family_send.open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              {fam.family_send.open && renderFamFields('family_send', true)}
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                type="button"
                onClick={() => updateFam('caregiving', { open: !fam.caregiving.open })}
                className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-[#1E293B]"
              >
                Caregiving costs
                {fam.caregiving.open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              {fam.caregiving.open && renderFamFields('caregiving', true)}
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
        className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save & Continue'}
      </button>

      <button
        type="button"
        onClick={() => {
          setPageError(null);
          onSkip();
        }}
        className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
      >
        I&apos;ll set this up later
      </button>
    </form>
  );
}
