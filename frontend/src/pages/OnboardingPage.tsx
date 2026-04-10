import React, { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import { useOnboarding } from '../hooks/useOnboarding';

const BG = '#0d0a08';
const GOLD = '#C4A064';
const TEXT = '#F0E8D8';

const STEP_META = [
  { step: 1, key: 'personal' as const, label: 'About You' },
  { step: 2, key: 'income' as const, label: 'Income' },
  { step: 3, key: 'expenses' as const, label: 'Expenses' },
  { step: 4, key: 'position' as const, label: 'Financial Position' },
  { step: 5, key: 'goals' as const, label: 'Goals' },
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
  'w-full rounded-lg border border-stone-600 bg-[#1a1512] px-3 py-2.5 text-[#F0E8D8] placeholder:text-stone-500 focus:border-[#C4A064] focus:outline-none focus:ring-1 focus:ring-[#C4A064]';

const labelClass = 'mb-1.5 block text-sm font-medium text-[#F0E8D8]/90';

export default function OnboardingPage() {
  const navigate = useNavigate();
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
  } = useOnboarding();

  /* Step 1 */
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

  /* Step 2 */
  const [incomeRows, setIncomeRows] = useState<IncomeRow[]>([
    { id: newId(), name: '', amount: '', frequency: 'monthly' },
  ]);

  /* Step 3 */
  const [expenseRows, setExpenseRows] = useState<ExpenseRow[]>(() =>
    PRESET_EXPENSES.map((p) => ({ ...p, id: newId(), amount: '0' }))
  );

  /* Step 4 */
  const [emergencyFund, setEmergencyFund] = useState('');
  const [creditScore, setCreditScore] = useState('');
  const [totalDebt, setTotalDebt] = useState('');
  const [savingsBalance, setSavingsBalance] = useState('');

  /* Step 5 */
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
      goToStep(5);
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
          <div key={key} className="flex flex-1 flex-col items-center gap-2 text-center">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors ${
                done
                  ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                  : active
                    ? 'border-[#C4A064] bg-[#C4A064]/10 text-[#C4A064]'
                    : 'border-stone-600 bg-[#1a1512] text-stone-500'
              }`}
              style={active ? { boxShadow: `0 0 0 1px ${GOLD}` } : undefined}
            >
              {done ? <Check className="h-5 w-5" strokeWidth={2.5} /> : step}
            </div>
            <span
              className={`max-w-[4.5rem] text-[10px] font-medium leading-tight sm:text-xs ${
                active ? 'text-[#C4A064]' : done ? 'text-stone-500' : 'text-stone-600'
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
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ backgroundColor: BG }}
      >
        <p className="text-[#F0E8D8]/70">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-8" style={{ backgroundColor: BG }}>
      <div className="mx-auto max-w-2xl rounded-2xl bg-[#0f172a] p-6 shadow-xl sm:p-8">
        {currentStep > 1 && (
          <button
            type="button"
            onClick={() => goToStep(currentStep - 1)}
            className="mb-6 text-sm text-stone-400 transition hover:text-[#F0E8D8]"
          >
            ← Back
          </button>
        )}

        <div className="mb-10 flex justify-between gap-1 sm:gap-2">{progressNodes}</div>

        {error && (
          <div
            className="mb-6 rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Step 1 */}
        {currentStep === 1 && (
          <form onSubmit={onSubmitPersonal} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold sm:text-3xl" style={{ color: TEXT }}>
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
                  <p className="mt-1 text-xs text-red-400">Use exactly 5 digits.</p>
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
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-[#C4A064] to-amber-600 py-3 font-semibold text-[#0d0a08] transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            {currentStep < 5 && (
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  skipStep();
                }}
                className="mt-3 w-full text-center text-sm text-stone-500 hover:text-stone-400"
              >
                Skip this step →
              </button>
            )}
          </form>
        )}

        {/* Step 2 */}
        {currentStep === 2 && (
          <form onSubmit={onSubmitIncome} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold sm:text-3xl" style={{ color: TEXT }}>
              Your income
            </h1>
            <p className="text-sm text-stone-400">
              This helps us calculate your savings rate and financial health score. Monthly take-home after tax.
            </p>
            <div className="space-y-4">
              {incomeRows.map((row, idx) => (
                <div
                  key={row.id}
                  className="relative rounded-xl border border-stone-700 bg-[#1a1512]/80 p-4"
                >
                  {incomeRows.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeIncomeRow(row.id)}
                      className="absolute right-2 top-2 rounded p-1 text-stone-500 hover:bg-stone-800 hover:text-red-400"
                      aria-label="Remove income source"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                  <p className="mb-2 text-xs font-medium text-stone-500">Source {idx + 1}</p>
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
              className="text-sm font-medium text-[#C4A064] hover:underline"
            >
              + Add another income source
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-[#C4A064] to-amber-600 py-3 font-semibold text-[#0d0a08] transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="mt-3 w-full text-center text-sm text-stone-500 hover:text-stone-400"
            >
              Skip this step →
            </button>
          </form>
        )}

        {/* Step 3 */}
        {currentStep === 3 && (
          <form onSubmit={onSubmitExpenses} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold sm:text-3xl" style={{ color: TEXT }}>
              Your monthly expenses
            </h1>
            <p className="text-sm text-stone-400">Estimates are fine — you can update these anytime.</p>
            <div className="space-y-4">
              {expenseRows.map((row) => (
                <div key={row.id} className="rounded-xl border border-stone-700 bg-[#1a1512]/80 p-4">
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
                        className="rounded p-1 text-stone-500 hover:bg-stone-800 hover:text-red-400"
                        aria-label="Remove expense"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addCustomExpense}
              className="text-sm font-medium text-[#C4A064] hover:underline"
            >
              + Add custom expense
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-[#C4A064] to-amber-600 py-3 font-semibold text-[#0d0a08] transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="mt-3 w-full text-center text-sm text-stone-500 hover:text-stone-400"
            >
              Skip this step →
            </button>
          </form>
        )}

        {/* Step 4 */}
        {currentStep === 4 && (
          <form onSubmit={onSubmitPosition} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold sm:text-3xl" style={{ color: TEXT }}>
              Where do you stand today?
            </h1>
            <p className="text-sm text-stone-400">
              A snapshot of your current financial position. All fields are optional — enter what you know.
            </p>
            <div>
              <label className={labelClass}>Emergency Fund Balance ($)</label>
              <p className="mb-1 text-xs text-stone-500">Total savings you could access in an emergency</p>
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
              <p className="mb-1 text-xs text-stone-500">Approximate is fine (300–850)</p>
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
              <p className="mb-1 text-xs text-stone-500">
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
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-[#C4A064] to-amber-600 py-3 font-semibold text-[#0d0a08] transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save & Continue'}
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                skipStep();
              }}
              className="mt-3 w-full text-center text-sm text-stone-500 hover:text-stone-400"
            >
              Skip this step →
            </button>
          </form>
        )}

        {/* Step 5 */}
        {currentStep === 5 && (
          <form onSubmit={onSubmitGoals} className="space-y-4">
            <h1 className="font-serif text-2xl font-semibold sm:text-3xl" style={{ color: TEXT }}>
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
              <p className="mb-1 text-xs text-stone-500">How much do you want to save each month?</p>
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
                {stressLevel !== '' && (
                  <span className="text-[#C4A064]">({stressLevel} / 10)</span>
                )}
              </label>
              <p className="mb-1 text-xs text-stone-500">How stressed do you feel about money right now?</p>
              <input
                className="mt-2 w-full accent-[#C4A064]"
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
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-[#C4A064] to-amber-600 py-3 font-semibold text-[#0d0a08] transition hover:opacity-95 disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Complete Setup'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="mt-3 w-full text-center text-sm text-stone-500 hover:text-stone-400"
            >
              Go straight to dashboard
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
