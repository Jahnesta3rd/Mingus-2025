import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useOnboarding } from '../hooks/useOnboarding';
import IncomeScheduleStep from '../components/onboarding/IncomeScheduleStep';
import ExpenseScheduleStep from '../components/onboarding/ExpenseScheduleStep';
import RosterSeedStep from '../components/onboarding/RosterSeedStep';
import QuickVibeStep from '../components/onboarding/QuickVibeStep';
import { csrfHeaders } from '../utils/csrfHeaders';

const STEP_META = [
  { step: 1, key: 'personal' as const, label: 'About You' },
  { step: 2, key: 'roster_seed' as const, label: 'Roster' },
  { step: 3, key: 'quick_vibe' as const, label: 'Vibe' },
  { step: 4, key: 'income' as const, label: 'Income' },
  { step: 5, key: 'income_schedule' as const, label: 'Paydays' },
  { step: 6, key: 'expense_schedule' as const, label: 'Bills' },
  { step: 7, key: 'expenses' as const, label: 'Expenses' },
  { step: 8, key: 'position' as const, label: 'Position' },
  { step: 9, key: 'goals' as const, label: 'Goals' },
];

const EXPENSE_DB_CATEGORIES = [
  'housing',
  'transportation',
  'insurance',
  'debt',
  'subscription',
  'utilities',
  'other',
  'relationship',
] as const;

function newId(): string {
  return crypto.randomUUID();
}

type IncomeRow = { id: string; name: string; amount: string; frequency: string };
type ExpenseRow = {
  id: string;
  name: string;
  amount: string;
  category: string;
  frequency: string;
  preset: boolean;
};

const PRESET_EXPENSES: Omit<ExpenseRow, 'id' | 'amount'>[] = [
  { name: 'Housing (rent or mortgage)', category: 'housing', frequency: 'monthly', preset: true },
  { name: 'Car / transportation', category: 'transportation', frequency: 'monthly', preset: true },
  { name: 'Groceries & food', category: 'other', frequency: 'monthly', preset: true },
  { name: 'Utilities', category: 'utilities', frequency: 'monthly', preset: true },
  { name: 'Subscriptions', category: 'subscription', frequency: 'monthly', preset: true },
  { name: 'Healthcare / insurance', category: 'insurance', frequency: 'monthly', preset: true },
  { name: 'Childcare', category: 'other', frequency: 'monthly', preset: true },
  { name: 'Debt payments', category: 'debt', frequency: 'monthly', preset: true },
];

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';

const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const {
    currentStep,
    stepsCompleted,
    isLoading,
    isSaving,
    error,
    setError,
    savePersonal,
    saveIncome,
    saveExpenses,
    savePosition,
    saveGoals,
    goToStep,
    skipStep,
    refreshSetupStatus,
    saveOnboardingFlags,
  } = useOnboarding();

  const [rosterFirstPerson, setRosterFirstPerson] = useState<{ id: string; nickname: string } | null>(
    null
  );

  useEffect(() => {
    if (currentStep !== 3) return;
    if (rosterFirstPerson) return;

    let cancelled = false;
    (async () => {
      const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
      const token = getAccessToken();
      if (token) h.Authorization = `Bearer ${token}`;
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'GET',
        credentials: 'include',
        headers: h,
      });
      if (cancelled) return;
      if (!res.ok) {
        goToStep(4);
        return;
      }
      const data = (await res.json()) as { people?: { id: string; nickname: string }[] };
      const list = data.people;
      if (Array.isArray(list) && list.length > 0) {
        setRosterFirstPerson({ id: list[0].id, nickname: list[0].nickname });
      } else {
        goToStep(4);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [currentStep, rosterFirstPerson, goToStep, getAccessToken]);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [city, setCity] = useState('');
  const [stateAbbr, setStateAbbr] = useState('');
  const [zip, setZip] = useState('');
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('');
  const [employmentStatus, setEmploymentStatus] = useState('');
  const [occupation, setOccupation] = useState('');
  const [employer, setEmployer] = useState('');

  const [incomeRows, setIncomeRows] = useState<IncomeRow[]>([
    { id: newId(), name: '', amount: '', frequency: 'monthly' },
  ]);

  const [expenseRows, setExpenseRows] = useState<ExpenseRow[]>(() =>
    PRESET_EXPENSES.map((p) => ({ ...p, id: newId(), amount: '0' }))
  );

  const [emergencyFund, setEmergencyFund] = useState('');
  const [creditScore, setCreditScore] = useState('');
  const [totalDebt, setTotalDebt] = useState('');
  const [savingsBalance, setSavingsBalance] = useState('');

  const [primaryGoal, setPrimaryGoal] = useState('');
  const [targetSavings, setTargetSavings] = useState('');
  const [stressLevel, setStressLevel] = useState<number | ''>('');

  const zipValid = zip === '' || /^\d{5}$/.test(zip);

  const addIncomeRow = useCallback(() => {
    setIncomeRows((r) => [...r, { id: newId(), name: '', amount: '', frequency: 'monthly' }]);
  }, []);

  const removeIncomeRow = useCallback((id: string) => {
    setIncomeRows((r) => (r.length <= 1 ? r : r.filter((x) => x.id !== id)));
  }, []);

  const addCustomExpense = useCallback(() => {
    setExpenseRows((r) => [
      ...r,
      {
        id: newId(),
        name: '',
        amount: '0',
        category: 'other',
        frequency: 'monthly',
        preset: false,
      },
    ]);
  }, []);

  const removeExpenseRow = useCallback((id: string) => {
    setExpenseRows((r) => {
      const row = r.find((x) => x.id === id);
      if (row?.preset) return r;
      return r.filter((x) => x.id !== id);
    });
  }, []);

  const onSubmitPersonal = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!firstName.trim() || !lastName.trim() || !city.trim() || !stateAbbr.trim() || !zip.trim()) {
      setError('Please fill all required fields.');
      return;
    }
    if (!/^\d{5}$/.test(zip)) {
      setError('ZIP code must be exactly 5 digits.');
      return;
    }
    if (!employmentStatus) {
      setError('Please select employment status.');
      return;
    }
    await savePersonal({
      personalInfo: {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        city: city.trim(),
        state: stateAbbr.trim().toUpperCase(),
        zip: zip.trim(),
        phone: phone.trim() || undefined,
        dateOfBirth: dob || undefined,
        employmentStatus,
        occupation: occupation.trim() || undefined,
        employer: employer.trim() || undefined,
      },
    });
  };

  const onSubmitIncome = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const sources = incomeRows
      .map((r) => ({
        source_name: r.name.trim(),
        amount: parseFloat(r.amount),
        frequency: r.frequency,
      }))
      .filter((s) => s.source_name.length > 0);
    if (sources.length < 1) {
      setError('Add at least one income source.');
      return;
    }
    if (sources.some((s) => !Number.isFinite(s.amount) || s.amount <= 0)) {
      setError('Each income source needs an amount greater than 0.');
      return;
    }
    await saveIncome({ sources });
  };

  const onSubmitExpenses = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const expenses = expenseRows
      .filter((r) => {
        const a = parseFloat(r.amount);
        return Number.isFinite(a) && a > 0;
      })
      .map((r) => ({
        name: r.name.trim() || 'Expense',
        amount: parseFloat(r.amount),
        category: r.category,
        frequency: r.frequency,
      }));
    if (expenses.length < 1) {
      setError('Enter at least one expense with an amount greater than 0.');
      return;
    }
    await saveExpenses({ expenses });
  };

  const onSubmitPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const payload: Record<string, number | null> = {};
    if (emergencyFund !== '') {
      const v = parseFloat(emergencyFund);
      if (!Number.isFinite(v) || v < 0) {
        setError('Emergency fund must be a number ≥ 0.');
        return;
      }
      payload.emergency_fund = v;
    }
    if (creditScore !== '') {
      const v = parseInt(creditScore, 10);
      if (!Number.isFinite(v) || v < 300 || v > 850) {
        setError('Credit score must be between 300 and 850.');
        return;
      }
      payload.credit_score = v;
    }
    if (totalDebt !== '') {
      const v = parseFloat(totalDebt);
      if (!Number.isFinite(v)) {
        setError('Total debt must be a number.');
        return;
      }
      payload.total_debt = v;
    }
    if (savingsBalance !== '') {
      const v = parseFloat(savingsBalance);
      if (!Number.isFinite(v)) {
        setError('Savings balance must be a number.');
        return;
      }
      payload.savings_balance = v;
    }
    const hasAny = Object.keys(payload).length > 0;
    const ok = await savePosition(payload);
    if (ok && !hasAny) {
      goToStep(9);
    }
  };

  const onSubmitGoals = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!primaryGoal) {
      setError('Please choose a primary goal.');
      return;
    }
    const goalsObj: Record<string, unknown> = { primaryGoal };
    if (targetSavings !== '') {
      const v = parseFloat(targetSavings);
      if (Number.isFinite(v)) goalsObj.targetMonthlySavings = v;
    }
    if (stressLevel !== '') {
      goalsObj.financialStressLevel = stressLevel;
    }
    const ok = await saveGoals({ goals: goalsObj });
    if (ok) {
      navigate('/dashboard');
    }
  };

  const progressNodes = useMemo(
    () =>
      STEP_META.map(({ step, key, label }) => {
        const done = stepsCompleted.includes(key);
        const active = currentStep === step;
        return (
          <div key={key} className="flex flex-1 flex-col items-center gap-2 text-center min-w-[2.75rem]">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors sm:text-sm ${
                done
                  ? 'border-[#059669] bg-emerald-50 text-[#059669]'
                  : active
                    ? 'border-[#5B2D8E] bg-[#EDE9FE] text-[#5B2D8E]'
                    : 'border-[#E2E8F0] bg-white text-[#64748B]'
              }`}
            >
              {done ? <Check className="h-5 w-5" strokeWidth={2.5} /> : step}
            </div>
            <span
              className={`max-w-[3.5rem] text-[9px] font-medium leading-tight sm:max-w-[4.5rem] sm:text-[10px] ${
                active ? 'text-[#5B2D8E]' : done ? 'text-[#64748B]' : 'text-[#94A3B8]'
              }`}
            >
              {label}
            </span>
          </div>
        );
      }),
    [currentStep, stepsCompleted]
  );

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC]">
        <div className="w-full max-w-md space-y-3 rounded-xl border border-[#E2E8F0] bg-white p-8 shadow-sm">
          <div className="h-4 w-3/4 animate-pulse rounded bg-[#E2E8F0]" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-[#E2E8F0]" />
          <div className="h-10 w-full animate-pulse rounded-lg bg-[#E2E8F0]" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] px-4 py-8">
      <div className="mx-auto max-w-2xl rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-sm sm:p-8">
        {currentStep > 1 && (
          <button
            type="button"
            onClick={() => goToStep(currentStep - 1)}
            className="mb-6 min-h-11 text-sm text-[#64748B] transition hover:text-[#1E293B]"
          >
            ← Back
          </button>
        )}

        <div className="mb-10 flex flex-wrap justify-between gap-2 sm:gap-1">{progressNodes}</div>

        {error && (
          <div
            className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-[#DC2626]"
            role="alert"
          >
            {error}
          </div>
        )}

        {currentStep === 1 && (
          <form onSubmit={onSubmitPersonal} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
              Tell us about yourself
            </h1>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass}>First Name *</label>
                <input
                  className={inputClass}
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className={labelClass}>Last Name *</label>
                <input
                  className={inputClass}
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
            </div>
            <div>
              <label className={labelClass}>City *</label>
              <input className={inputClass} value={city} onChange={(e) => setCity(e.target.value)} required />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass}>State * (2 letters)</label>
                <input
                  className={inputClass}
                  value={stateAbbr}
                  onChange={(e) => setStateAbbr(e.target.value.slice(0, 2))}
                  maxLength={2}
                  required
                />
              </div>
              <div>
                <label className={labelClass}>ZIP Code *</label>
                <input
                  className={inputClass}
                  value={zip}
                  onChange={(e) => setZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
                  inputMode="numeric"
                  pattern="\d{5}"
                  required
                />
                {!zipValid && zip.length > 0 && (
                  <p className="mt-1 text-xs text-[#DC2626]">Use exactly 5 digits.</p>
                )}
              </div>
            </div>
            <div>
              <label className={labelClass}>Phone</label>
              <input className={inputClass} value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Date of Birth</label>
              <input className={inputClass} type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Employment Status *</label>
              <select
                className={inputClass}
                value={employmentStatus}
                onChange={(e) => setEmploymentStatus(e.target.value)}
                required
              >
                <option value="">Select…</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="self-employed">Self-employed</option>
                <option value="contract">Contract</option>
                <option value="unemployed">Unemployed</option>
                <option value="retired">Retired</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Occupation</label>
              <input className={inputClass} value={occupation} onChange={(e) => setOccupation(e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>Employer</label>
              <input className={inputClass} value={employer} onChange={(e) => setEmployer(e.target.value)} />
            </div>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
            >
              Skip this step →
            </button>
          </form>
        )}

        {currentStep === 2 && (
          <RosterSeedStep
            onSubmitted={async (first) => {
              setRosterFirstPerson(first);
              await refreshSetupStatus();
              goToStep(3);
            }}
            onSkip={async () => {
              setError(null);
              const ok = await saveOnboardingFlags({
                roster_seed_skipped: true,
                quick_vibe_skipped: true,
              });
              if (ok) goToStep(4);
            }}
            setPageError={setError}
          />
        )}

        {currentStep === 3 && rosterFirstPerson && (
          <QuickVibeStep
            personId={rosterFirstPerson.id}
            nickname={rosterFirstPerson.nickname}
            onAdvance={() => goToStep(4)}
            onSkip={async () => {
              setError(null);
              const ok = await saveOnboardingFlags({ quick_vibe_skipped: true });
              if (ok) goToStep(4);
            }}
            setPageError={setError}
            onRefreshSetup={refreshSetupStatus}
          />
        )}

        {currentStep === 3 && !rosterFirstPerson && (
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-8 shadow-sm">
            <div className="h-5 w-2/3 animate-pulse rounded bg-[#E2E8F0]" />
            <div className="mt-4 h-24 animate-pulse rounded-xl bg-[#F8FAFC]" />
          </div>
        )}

        {currentStep === 4 && (
          <form onSubmit={onSubmitIncome} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Your income</h1>
            <p className="text-sm text-[#64748B]">
              This helps us calculate your savings rate and financial health score. Monthly take-home after tax.
            </p>
            <div className="space-y-4">
              {incomeRows.map((row, idx) => (
                <div key={row.id} className="relative rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
                  {incomeRows.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeIncomeRow(row.id)}
                      className="absolute right-2 top-2 min-h-11 min-w-11 rounded p-1 text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#DC2626]"
                      aria-label="Remove income source"
                    >
                      <X className="mx-auto h-4 w-4" />
                    </button>
                  )}
                  <p className="mb-2 text-xs font-medium text-[#64748B]">Source {idx + 1}</p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="sm:col-span-2">
                      <label className={labelClass}>Source Name</label>
                      <input
                        className={inputClass}
                        placeholder="e.g. Primary Job"
                        value={row.name}
                        onChange={(e) =>
                          setIncomeRows((r) =>
                            r.map((x) => (x.id === row.id ? { ...x, name: e.target.value } : x))
                          )
                        }
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Monthly take-home ($)</label>
                      <input
                        className={inputClass}
                        type="number"
                        min={0}
                        step="0.01"
                        value={row.amount}
                        onChange={(e) =>
                          setIncomeRows((r) =>
                            r.map((x) => (x.id === row.id ? { ...x, amount: e.target.value } : x))
                          )
                        }
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Pay frequency</label>
                      <select
                        className={inputClass}
                        value={row.frequency}
                        onChange={(e) =>
                          setIncomeRows((r) =>
                            r.map((x) => (x.id === row.id ? { ...x, frequency: e.target.value } : x))
                          )
                        }
                      >
                        <option value="monthly">Monthly</option>
                        <option value="biweekly">Biweekly</option>
                        <option value="weekly">Weekly</option>
                        <option value="annual">Annual</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addIncomeRow}
              className="min-h-11 text-sm font-medium text-[#6D28D9] hover:underline"
            >
              + Add another income source
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
            >
              Skip this step →
            </button>
          </form>
        )}

        {currentStep === 5 && (
          <IncomeScheduleStep
            onContinue={() => goToStep(6)}
            onSkip={() => {
              setError(null);
              skipStep();
            }}
            onRefreshSetup={refreshSetupStatus}
            setPageError={setError}
          />
        )}

        {currentStep === 6 && (
          <ExpenseScheduleStep
            onContinue={() => goToStep(7)}
            onSkip={() => {
              setError(null);
              skipStep();
            }}
            onRefreshSetup={refreshSetupStatus}
            setPageError={setError}
          />
        )}

        {currentStep === 7 && (
          <form onSubmit={onSubmitExpenses} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
              Your monthly expenses
            </h1>
            <p className="text-sm text-[#64748B]">Estimates are fine — you can update these anytime.</p>
            <div className="space-y-4">
              {expenseRows.map((row) => (
                <div key={row.id} className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="grid flex-1 gap-3 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <label className={labelClass}>Name</label>
                        <input
                          className={inputClass}
                          value={row.name}
                          onChange={(e) =>
                            setExpenseRows((r) =>
                              r.map((x) => (x.id === row.id ? { ...x, name: e.target.value } : x))
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className={labelClass}>Amount ($)</label>
                        <input
                          className={inputClass}
                          type="number"
                          min={0}
                          step="0.01"
                          value={row.amount}
                          onChange={(e) =>
                            setExpenseRows((r) =>
                              r.map((x) => (x.id === row.id ? { ...x, amount: e.target.value } : x))
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className={labelClass}>Frequency</label>
                        <select
                          className={inputClass}
                          value={row.frequency}
                          onChange={(e) =>
                            setExpenseRows((r) =>
                              r.map((x) => (x.id === row.id ? { ...x, frequency: e.target.value } : x))
                            )
                          }
                        >
                          <option value="monthly">Monthly</option>
                          <option value="weekly">Weekly</option>
                          <option value="biweekly">Biweekly</option>
                          <option value="annual">Annual</option>
                        </select>
                      </div>
                      {!row.preset && (
                        <div className="sm:col-span-2">
                          <label className={labelClass}>Category</label>
                          <select
                            className={inputClass}
                            value={row.category}
                            onChange={(e) =>
                              setExpenseRows((r) =>
                                r.map((x) => (x.id === row.id ? { ...x, category: e.target.value } : x))
                              )
                            }
                          >
                            {EXPENSE_DB_CATEGORIES.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                    </div>
                    {!row.preset && (
                      <button
                        type="button"
                        onClick={() => removeExpenseRow(row.id)}
                        className="min-h-11 min-w-11 rounded p-1 text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#DC2626]"
                        aria-label="Remove expense"
                      >
                        <X className="mx-auto h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addCustomExpense}
              className="min-h-11 text-sm font-medium text-[#6D28D9] hover:underline"
            >
              + Add custom expense
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
            >
              Skip this step →
            </button>
          </form>
        )}

        {currentStep === 8 && (
          <form onSubmit={onSubmitPosition} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
              Where do you stand today?
            </h1>
            <p className="text-sm text-[#64748B]">
              A snapshot of your current financial position. All fields are optional — enter what you know.
            </p>
            <div>
              <label className={labelClass}>Emergency Fund Balance ($)</label>
              <p className="mb-1 text-xs text-[#64748B]">Total savings you could access in an emergency</p>
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={emergencyFund}
                onChange={(e) => setEmergencyFund(e.target.value)}
              />
            </div>
            <div>
              <label className={labelClass}>Credit Score (optional)</label>
              <p className="mb-1 text-xs text-[#64748B]">Approximate is fine (300–850)</p>
              <input
                className={inputClass}
                type="number"
                min={300}
                max={850}
                value={creditScore}
                onChange={(e) => setCreditScore(e.target.value)}
              />
            </div>
            <div>
              <label className={labelClass}>Total Debt ($) (optional)</label>
              <p className="mb-1 text-xs text-[#64748B]">
                Credit cards, student loans, car loans, etc. (excluding mortgage)
              </p>
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={totalDebt}
                onChange={(e) => setTotalDebt(e.target.value)}
              />
            </div>
            <div>
              <label className={labelClass}>Current Savings Balance ($) (optional)</label>
              <input
                className={inputClass}
                type="number"
                step="0.01"
                value={savingsBalance}
                onChange={(e) => setSavingsBalance(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
            >
              Skip this step →
            </button>
          </form>
        )}

        {currentStep === 9 && (
          <form onSubmit={onSubmitGoals} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
              What are you working toward?
            </h1>
            <div>
              <label className={labelClass}>Primary Goal *</label>
              <select
                className={inputClass}
                value={primaryGoal}
                onChange={(e) => setPrimaryGoal(e.target.value)}
                required
              >
                <option value="">Select…</option>
                <option value="emergency_fund">Build / grow emergency fund</option>
                <option value="pay_debt">Pay off debt</option>
                <option value="investing">Start investing</option>
                <option value="major_purchase">Save for a major purchase</option>
                <option value="credit_score">Improve my credit score</option>
                <option value="awareness">Understand where my money goes</option>
                <option value="habits">Build better financial habits</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Target Monthly Savings ($) (optional)</label>
              <p className="mb-1 text-xs text-[#64748B]">How much do you want to save each month?</p>
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={targetSavings}
                onChange={(e) => setTargetSavings(e.target.value)}
              />
            </div>
            <div>
              <label className={labelClass}>
                Financial stress level (optional){' '}
                {stressLevel !== '' && <span className="text-[#5B2D8E]">({stressLevel} / 10)</span>}
              </label>
              <p className="mb-1 text-xs text-[#64748B]">How stressed do you feel about money right now?</p>
              <input
                className="mt-2 h-11 w-full accent-[#5B2D8E]"
                type="range"
                min={1}
                max={10}
                step={1}
                value={stressLevel === '' ? 5 : stressLevel}
                onChange={(e) => setStressLevel(Number(e.target.value))}
              />
            </div>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Complete Setup'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="min-h-11 w-full text-center text-sm text-[#64748B] hover:text-[#1E293B]"
            >
              Go straight to dashboard
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
