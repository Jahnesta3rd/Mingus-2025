import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, Loader2, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { csrfHeaders } from '../utils/csrfHeaders';

export interface DebtAnalyzerTabProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
  className?: string;
}

type SubTab = 'analyzer' | 'second-job';
type SchedulePreference =
  | 'flexible'
  | 'evenings_weekends'
  | 'weekends'
  | 'mornings'
  | 'remote';

interface DebtProfile {
  has_profile: boolean;
  revolving_balance?: number | null;
  revolving_apr?: number | null;
  revolving_min_payment?: number | null;
  revolving_apr_unknown?: boolean;
  installment_balance?: number | null;
  installment_apr?: number | null;
  installment_payment?: number | null;
  federal_student_balance?: number | null;
  federal_student_payment?: number | null;
  on_idr_plan?: boolean;
  pursuing_pslf?: boolean;
  private_student_balance?: number | null;
  private_student_apr?: number | null;
  bnpl_balance?: number | null;
  bnpl_monthly_payment?: number | null;
  bnpl_active_plans?: number | null;
}

interface StrategyResult {
  payoff_months: number;
  total_interest: number;
  payoff_order: string[];
  monthly_schedule: { month: number; remaining_total: number; interest_paid: number }[];
}

interface CalculateResponse {
  total_debt: number;
  analyzer_debt: number;
  monthly_payment: number;
  strategies: {
    avalanche: StrategyResult;
    snowball: StrategyResult;
    hybrid: StrategyResult;
  };
  federal_student_loans: {
    balance: number;
    monthly_payment: number;
    on_idr_plan: boolean;
    pursuing_pslf: boolean;
    recommendation: string;
  };
  bnpl_flagged: boolean;
  recommended_strategy: 'avalanche' | 'snowball' | 'hybrid';
  interest_savings_vs_minimum: number;
  partial_data: boolean;
}

interface SecondJob {
  title: string;
  type: 'gig' | 'part_time' | 'freelance' | 'contract';
  hourly_range: string;
  hours_per_week: number;
  monthly_est: number;
  schedule_fit: string;
  why_it_fits: string;
  debt_impact: string;
  first_step: string;
  startup_cost: string;
}

interface SecondJobResponse {
  jobs: SecondJob[];
  monthly_potential: number;
  disclaimer: string;
}

interface FormState {
  revolving_balance: string;
  revolving_apr: string;
  revolving_min_payment: string;
  revolving_apr_unknown: boolean;
  installment_balance: string;
  installment_apr: string;
  installment_payment: string;
  federal_student_balance: string;
  federal_student_payment: string;
  on_idr_plan: boolean;
  pursuing_pslf: boolean;
  private_student_balance: string;
  private_student_apr: string;
  bnpl_balance: string;
  bnpl_monthly_payment: string;
  bnpl_active_plans: string;
}

const EMPTY_FORM: FormState = {
  revolving_balance: '',
  revolving_apr: '',
  revolving_min_payment: '',
  revolving_apr_unknown: false,
  installment_balance: '',
  installment_apr: '',
  installment_payment: '',
  federal_student_balance: '',
  federal_student_payment: '',
  on_idr_plan: false,
  pursuing_pslf: false,
  private_student_balance: '',
  private_student_apr: '',
  bnpl_balance: '',
  bnpl_monthly_payment: '',
  bnpl_active_plans: '',
};

const SCHEDULE_OPTIONS: { value: SchedulePreference; label: string }[] = [
  { value: 'flexible', label: 'Flexible' },
  { value: 'evenings_weekends', label: 'Evenings & weekends' },
  { value: 'weekends', label: 'Weekends only' },
  { value: 'mornings', label: 'Mornings' },
  { value: 'remote', label: 'Remote/online' },
];

const STRATEGY_ORDER = ['avalanche', 'snowball', 'hybrid'] as const;
type StrategyKey = (typeof STRATEGY_ORDER)[number];

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  return {
    ...csrfHeaders(),
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function parseNum(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : undefined;
}

function profileToForm(profile: DebtProfile): FormState {
  return {
    revolving_balance: profile.revolving_balance != null ? String(profile.revolving_balance) : '',
    revolving_apr: profile.revolving_apr != null ? String(profile.revolving_apr) : '',
    revolving_min_payment:
      profile.revolving_min_payment != null ? String(profile.revolving_min_payment) : '',
    revolving_apr_unknown: Boolean(profile.revolving_apr_unknown),
    installment_balance:
      profile.installment_balance != null ? String(profile.installment_balance) : '',
    installment_apr: profile.installment_apr != null ? String(profile.installment_apr) : '',
    installment_payment:
      profile.installment_payment != null ? String(profile.installment_payment) : '',
    federal_student_balance:
      profile.federal_student_balance != null ? String(profile.federal_student_balance) : '',
    federal_student_payment:
      profile.federal_student_payment != null ? String(profile.federal_student_payment) : '',
    on_idr_plan: Boolean(profile.on_idr_plan),
    pursuing_pslf: Boolean(profile.pursuing_pslf),
    private_student_balance:
      profile.private_student_balance != null ? String(profile.private_student_balance) : '',
    private_student_apr:
      profile.private_student_apr != null ? String(profile.private_student_apr) : '',
    bnpl_balance: profile.bnpl_balance != null ? String(profile.bnpl_balance) : '',
    bnpl_monthly_payment:
      profile.bnpl_monthly_payment != null ? String(profile.bnpl_monthly_payment) : '',
    bnpl_active_plans:
      profile.bnpl_active_plans != null ? String(profile.bnpl_active_plans) : '',
  };
}

function formToPayload(form: FormState): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    revolving_apr_unknown: form.revolving_apr_unknown,
    on_idr_plan: form.on_idr_plan,
    pursuing_pslf: form.pursuing_pslf,
  };

  const numericFields: (keyof FormState)[] = [
    'revolving_balance',
    'revolving_apr',
    'revolving_min_payment',
    'installment_balance',
    'installment_apr',
    'installment_payment',
    'federal_student_balance',
    'federal_student_payment',
    'private_student_balance',
    'private_student_apr',
    'bnpl_balance',
    'bnpl_monthly_payment',
    'bnpl_active_plans',
  ];

  for (const field of numericFields) {
    if (field === 'revolving_apr' && form.revolving_apr_unknown) continue;
    const parsed = parseNum(form[field] as string);
    if (parsed !== undefined) payload[field] = parsed;
  }

  return payload;
}

function sumMinimumPayments(form: FormState): number {
  let total = 0;
  total += parseNum(form.revolving_min_payment) ?? 0;
  total += parseNum(form.installment_payment) ?? 0;
  total += parseNum(form.federal_student_payment) ?? 0;
  total += parseNum(form.bnpl_monthly_payment) ?? 0;
  const privateBal = parseNum(form.private_student_balance) ?? 0;
  if (privateBal > 0) total += privateBal * 0.02;
  return total;
}

function formatCurrency(amount: number): string {
  return `$${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function formatPayoffDuration(months: number): string {
  if (months <= 0) return '0 months';
  const years = Math.floor(months / 12);
  const rem = months % 12;
  if (years === 0) return `${rem} month${rem === 1 ? '' : 's'}`;
  if (rem === 0) return `${years} year${years === 1 ? '' : 's'}`;
  return `${years} year${years === 1 ? '' : 's'} ${rem} month${rem === 1 ? '' : 's'}`;
}

function formatJobType(type: SecondJob['type']): string {
  const map: Record<SecondJob['type'], string> = {
    gig: 'Gig',
    part_time: 'Part-time',
    freelance: 'Freelance',
    contract: 'Contract',
  };
  return map[type] ?? type;
}

function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
  onSkip,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  onSkip: () => void;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/50">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-semibold text-gray-800">{title}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-500" aria-hidden />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" aria-hidden />
        )}
      </button>
      {open ? (
        <div className="space-y-3 border-t border-gray-100 px-4 pb-4 pt-3">
          {children}
          <button
            type="button"
            onClick={onSkip}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Skip this section
          </button>
        </div>
      ) : null}
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  prefix,
  suffix,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  prefix?: string;
  suffix?: string;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-gray-700">{label}</span>
      <div className="flex items-center gap-1">
        {prefix ? <span className="text-sm text-gray-500">{prefix}</span> : null}
        <input
          type="number"
          min="0"
          step="any"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
        />
        {suffix ? <span className="text-sm text-gray-500">{suffix}</span> : null}
      </div>
      {hint ? <p className="mt-1 text-xs text-gray-500">{hint}</p> : null}
    </label>
  );
}

export function DebtAnalyzerTab({ userEmail: _userEmail, userTier, className = '' }: DebtAnalyzerTabProps) {
  const [subTab, setSubTab] = useState<SubTab>('analyzer');
  const [profileLoading, setProfileLoading] = useState(true);
  const [profile, setProfile] = useState<DebtProfile | null>(null);
  const [results, setResults] = useState<CalculateResponse | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [monthlyPayment, setMonthlyPayment] = useState('');
  const [extraPayment, setExtraPayment] = useState('0');
  const [analyzing, setAnalyzing] = useState(false);
  const [federalDismissed, setFederalDismissed] = useState(false);
  const [partialDismissed, setPartialDismissed] = useState(false);
  const autoModalShown = useRef(false);

  const [secondJobForm, setSecondJobForm] = useState({
    current_job: '',
    city: '',
    free_hours_per_week: '',
    schedule_preference: 'flexible' as SchedulePreference,
    skills: '',
    total_debt: '',
  });
  const [secondJobLoading, setSecondJobLoading] = useState(false);
  const [secondJobError, setSecondJobError] = useState(false);
  const [secondJobResults, setSecondJobResults] = useState<SecondJobResponse | null>(null);

  const isBudget = userTier === 'budget';
  const upgradePlansTo = '/dashboard/upgrade';

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    try {
      const res = await fetch('/api/debt-analyzer/profile', {
        credentials: 'include',
        headers: buildAuthHeaders(),
      });
      if (!res.ok) throw new Error('profile fetch failed');
      const data = (await res.json()) as DebtProfile;
      setProfile(data);
      if (data.has_profile) {
        setForm(profileToForm(data));
      }
    } catch {
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (
      !profileLoading &&
      profile?.has_profile &&
      !results &&
      !showForm &&
      !autoModalShown.current
    ) {
      autoModalShown.current = true;
      const savedForm = profileToForm(profile);
      setForm(savedForm);
      const prefilled = sumMinimumPayments(savedForm) + 100;
      setMonthlyPayment(String(Math.round(prefilled)));
      setExtraPayment('0');
      setShowPaymentModal(true);
    }
  }, [profileLoading, profile, results, showForm]);

  const runCalculate = useCallback(
    async (monthly: number, extra: number) => {
      setAnalyzing(true);
      try {
        const res = await fetch('/api/debt-analyzer/calculate', {
          method: 'POST',
          credentials: 'include',
          headers: buildAuthHeaders(),
          body: JSON.stringify({ monthly_payment: monthly, extra_payment: extra }),
        });
        if (!res.ok) throw new Error('calculate failed');
        const data = (await res.json()) as CalculateResponse;
        setResults(data);
        setShowForm(false);
        setShowPaymentModal(false);
      } catch {
        setResults(null);
      } finally {
        setAnalyzing(false);
      }
    },
    [],
  );

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/debt-analyzer/profile', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify(formToPayload(form)),
      });
      if (!res.ok) throw new Error('save failed');
      const data = (await res.json()) as { profile: DebtProfile };
      const saved = data.profile;
      setProfile(saved);
      setForm(profileToForm(saved));
      const prefilled = sumMinimumPayments(form) + 100;
      setMonthlyPayment(String(Math.round(prefilled)));
      setExtraPayment('0');
      setShowPaymentModal(true);
    } catch {
      // keep form visible on error
    } finally {
      setSaving(false);
    }
  };

  const skipSection = (section: 1 | 2 | 3 | 4 | 5) => {
    setForm((prev) => {
      const next = { ...prev };
      if (section === 1) {
        next.revolving_balance = '';
        next.revolving_apr = '';
        next.revolving_min_payment = '';
        next.revolving_apr_unknown = false;
      } else if (section === 2) {
        next.installment_balance = '';
        next.installment_apr = '';
        next.installment_payment = '';
      } else if (section === 3) {
        next.federal_student_balance = '';
        next.federal_student_payment = '';
        next.on_idr_plan = false;
        next.pursuing_pslf = false;
      } else if (section === 4) {
        next.private_student_balance = '';
        next.private_student_apr = '';
      } else {
        next.bnpl_balance = '';
        next.bnpl_monthly_payment = '';
        next.bnpl_active_plans = '';
      }
      return next;
    });
  };

  const openSecondJobTab = (totalDebt?: number) => {
    if (totalDebt != null) {
      setSecondJobForm((prev) => ({
        ...prev,
        total_debt: String(Math.round(totalDebt)),
      }));
    }
    setSubTab('second-job');
  };

  const fetchSecondJobs = async () => {
    if (!secondJobForm.current_job.trim() || !secondJobForm.free_hours_per_week.trim()) return;
    setSecondJobLoading(true);
    setSecondJobError(false);
    try {
      const body: Record<string, unknown> = {
        current_job: secondJobForm.current_job.trim(),
        free_hours_per_week: Number(secondJobForm.free_hours_per_week),
        schedule_preference: secondJobForm.schedule_preference,
      };
      if (secondJobForm.city.trim()) body.city = secondJobForm.city.trim();
      if (secondJobForm.skills.trim()) body.skills = secondJobForm.skills.trim();
      if (secondJobForm.total_debt.trim()) body.total_debt = Number(secondJobForm.total_debt);

      const res = await fetch('/api/second-job/suggest', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('suggest failed');
      setSecondJobResults((await res.json()) as SecondJobResponse);
    } catch {
      setSecondJobResults(null);
      setSecondJobError(true);
    } finally {
      setSecondJobLoading(false);
    }
  };

  const bnplBalance = useMemo(() => {
    if (profile?.bnpl_balance != null) return profile.bnpl_balance;
    return parseNum(form.bnpl_balance);
  }, [profile, form.bnpl_balance]);

  const showResults = Boolean(profile?.has_profile && results && !showForm);

  const renderDebtForm = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">
          Let&apos;s get a complete picture of your debt
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          Takes about 2 minutes. The more you share, the more accurate your payoff plan.
        </p>
      </div>

      <CollapsibleSection title="Credit Cards & Store Cards" defaultOpen onSkip={() => skipSection(1)}>
        <NumberField
          label="Total balance"
          prefix="$"
          value={form.revolving_balance}
          onChange={(v) => setForm((f) => ({ ...f, revolving_balance: v }))}
        />
        {!form.revolving_apr_unknown ? (
          <NumberField
            label="Average APR"
            suffix="%"
            value={form.revolving_apr}
            onChange={(v) => setForm((f) => ({ ...f, revolving_apr: v }))}
          />
        ) : null}
        <label className="flex items-start gap-2">
          <input
            type="checkbox"
            checked={form.revolving_apr_unknown}
            onChange={(e) =>
              setForm((f) => ({ ...f, revolving_apr_unknown: e.target.checked }))
            }
            className="mt-1 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-700">I don&apos;t know my APR</span>
        </label>
        {form.revolving_apr_unknown ? (
          <p className="text-xs text-amber-700">
            We&apos;ll use 22% as a conservative estimate
          </p>
        ) : null}
        <NumberField
          label="Minimum payments/month"
          prefix="$"
          value={form.revolving_min_payment}
          onChange={(v) => setForm((f) => ({ ...f, revolving_min_payment: v }))}
        />
      </CollapsibleSection>

      <CollapsibleSection title="Auto, Personal & Medical Loans" onSkip={() => skipSection(2)}>
        <NumberField
          label="Total balance"
          prefix="$"
          value={form.installment_balance}
          onChange={(v) => setForm((f) => ({ ...f, installment_balance: v }))}
        />
        <NumberField
          label="Average interest rate"
          suffix="%"
          value={form.installment_apr}
          onChange={(v) => setForm((f) => ({ ...f, installment_apr: v }))}
        />
        <NumberField
          label="Monthly payments"
          prefix="$"
          value={form.installment_payment}
          onChange={(v) => setForm((f) => ({ ...f, installment_payment: v }))}
        />
      </CollapsibleSection>

      <CollapsibleSection title="Federal Student Loans" onSkip={() => skipSection(3)}>
        <NumberField
          label="Total balance"
          prefix="$"
          value={form.federal_student_balance}
          onChange={(v) => setForm((f) => ({ ...f, federal_student_balance: v }))}
        />
        <NumberField
          label="Monthly payment"
          prefix="$"
          value={form.federal_student_payment}
          onChange={(v) => setForm((f) => ({ ...f, federal_student_payment: v }))}
          hint="Enter $0 if on income-driven repayment or deferment"
        />
        <label className="flex items-start gap-2">
          <input
            type="checkbox"
            checked={form.pursuing_pslf}
            onChange={(e) => setForm((f) => ({ ...f, pursuing_pslf: e.target.checked }))}
            className="mt-1 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-700">
            I&apos;m pursuing Public Service Loan Forgiveness (PSLF)
          </span>
        </label>
        <label className="flex items-start gap-2">
          <input
            type="checkbox"
            checked={form.on_idr_plan}
            onChange={(e) => setForm((f) => ({ ...f, on_idr_plan: e.target.checked }))}
            className="mt-1 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-700">
            I&apos;m on an income-driven repayment (IDR) plan
          </span>
        </label>
        <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
          Federal student loans are handled separately from your payoff strategy — they may
          qualify for forgiveness programs.
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="Private Student Loans" onSkip={() => skipSection(4)}>
        <NumberField
          label="Total balance"
          prefix="$"
          value={form.private_student_balance}
          onChange={(v) => setForm((f) => ({ ...f, private_student_balance: v }))}
        />
        <NumberField
          label="Interest rate"
          suffix="%"
          value={form.private_student_apr}
          onChange={(v) => setForm((f) => ({ ...f, private_student_apr: v }))}
        />
      </CollapsibleSection>

      <CollapsibleSection
        title="Buy Now, Pay Later"
        onSkip={() => skipSection(5)}
      >
        <p className="text-xs text-gray-500">Affirm, Klarna, Afterpay, etc.</p>
        <NumberField
          label="Total still owed"
          prefix="$"
          value={form.bnpl_balance}
          onChange={(v) => setForm((f) => ({ ...f, bnpl_balance: v }))}
        />
        <NumberField
          label="Monthly payments due"
          prefix="$"
          value={form.bnpl_monthly_payment}
          onChange={(v) => setForm((f) => ({ ...f, bnpl_monthly_payment: v }))}
        />
        <NumberField
          label="Number of active plans"
          value={form.bnpl_active_plans}
          onChange={(v) => setForm((f) => ({ ...f, bnpl_active_plans: v }))}
        />
        <div className="rounded-lg bg-red-50 p-3 text-xs text-red-700">
          We prioritize BNPL payoff before other debts — missed payments can carry penalties
          equivalent to 100%+ APR.
        </div>
      </CollapsibleSection>

      <button
        type="button"
        disabled={saving}
        onClick={() => void handleSaveProfile()}
        className="w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
      >
        {saving ? 'Saving…' : 'Save & Analyze'}
      </button>
    </div>
  );

  const renderStrategyCards = () => {
    if (!results) return null;
    const recommended = results.recommended_strategy;

    return (
      <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
        {STRATEGY_ORDER.map((key) => {
          const strategy = results.strategies[key];
          const isRecommended = key === recommended;
          const isHybridLocked = key === 'hybrid' && isBudget;

          return (
            <div
              key={key}
              className={`relative min-w-[240px] flex-shrink-0 rounded-xl border p-4 ${
                isRecommended ? 'border-teal-500 bg-teal-50' : 'border-gray-200 bg-white'
              } ${isHybridLocked ? 'overflow-hidden' : ''}`}
            >
              {isHybridLocked ? (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/70 px-4 text-center backdrop-blur-sm">
                  <p className="text-sm font-medium text-gray-700">
                    Upgrade to Mid-tier to unlock the Hybrid strategy
                  </p>
                  <Link
                    to={upgradePlansTo}
                    className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
                  >
                    View Plans →
                  </Link>
                </div>
              ) : null}
              <div className={isHybridLocked ? 'blur-sm select-none' : ''}>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-gray-900">{key.toUpperCase()}</h4>
                  {isRecommended ? (
                    <span className="rounded-full bg-teal-600 px-2 py-0.5 text-xs font-medium text-white">
                      Recommended
                    </span>
                  ) : null}
                </div>
                <p className="mt-3 text-2xl font-bold text-gray-900">
                  {formatPayoffDuration(strategy.payoff_months)}
                </p>
                <p className="mt-1 text-xs text-gray-500">Payoff in</p>
                <p className="mt-2 text-sm text-gray-600">
                  Total interest: {formatCurrency(strategy.total_interest)}
                </p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {strategy.payoff_order.map((name) => (
                    <span
                      key={name}
                      className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderResults = () => {
    if (!results) return null;
    const federal = results.federal_student_loans;

    return (
      <div className="space-y-4">
        {federal.balance > 0 && !federalDismissed ? (
          <div className="relative rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
            <button
              type="button"
              onClick={() => setFederalDismissed(true)}
              className="absolute right-3 top-3 text-amber-700 hover:text-amber-900"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
            <p>
              Your {formatCurrency(federal.balance)} in federal student loans are not included
              in the payoff strategies below. {federal.recommendation}
            </p>
          </div>
        ) : null}

        {results.bnpl_flagged && bnplBalance ? (
          <span className="inline-flex rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
            ⚠ Pay BNPL first — {formatCurrency(bnplBalance)} due
          </span>
        ) : null}

        {renderStrategyCards()}

        {results.interest_savings_vs_minimum > 0 ? (
          <div className="rounded-xl bg-green-50 p-3 text-sm text-green-800">
            Optimizing your payoff order saves you{' '}
            {formatCurrency(results.interest_savings_vs_minimum)} vs minimum payments
          </div>
        ) : null}

        {results.partial_data && !partialDismissed ? (
          <div className="relative rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
            <button
              type="button"
              onClick={() => setPartialDismissed(true)}
              className="absolute right-3 top-3 text-amber-700 hover:text-amber-900"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
            <p>
              Your APR was estimated at 22%. Update your debt profile for a more accurate
              analysis.{' '}
              <button
                type="button"
                onClick={() => setShowForm(true)}
                className="font-medium text-amber-900 underline"
              >
                Update profile →
              </button>
            </p>
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => openSecondJobTab(results.analyzer_debt)}
          className="text-sm font-medium text-teal-700 hover:text-teal-900"
        >
          Find a second job to pay this down faster →
        </button>
      </div>
    );
  };

  const renderSecondJobFinder = () => (
    <div className="space-y-4">
      <div className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-sm text-gray-700">
            Current job/field <span className="text-red-500">*</span>
          </span>
          <input
            type="text"
            value={secondJobForm.current_job}
            onChange={(e) =>
              setSecondJobForm((f) => ({ ...f, current_job: e.target.value }))
            }
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-gray-700">City/metro</span>
          <input
            type="text"
            value={secondJobForm.city}
            onChange={(e) => setSecondJobForm((f) => ({ ...f, city: e.target.value }))}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-gray-700">
            Free hours per week <span className="text-red-500">*</span>
          </span>
          <input
            type="number"
            min="1"
            value={secondJobForm.free_hours_per_week}
            onChange={(e) =>
              setSecondJobForm((f) => ({ ...f, free_hours_per_week: e.target.value }))
            }
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-gray-700">Schedule preference</span>
          <select
            value={secondJobForm.schedule_preference}
            onChange={(e) =>
              setSecondJobForm((f) => ({
                ...f,
                schedule_preference: e.target.value as SchedulePreference,
              }))
            }
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          >
            {SCHEDULE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-gray-700">Skills or interests</span>
          <input
            type="text"
            value={secondJobForm.skills}
            onChange={(e) => setSecondJobForm((f) => ({ ...f, skills: e.target.value }))}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
        </label>
        <NumberField
          label="Total debt"
          prefix="$"
          value={secondJobForm.total_debt}
          onChange={(v) => setSecondJobForm((f) => ({ ...f, total_debt: v }))}
        />
      </div>

      <button
        type="button"
        disabled={secondJobLoading}
        onClick={() => void fetchSecondJobs()}
        className="w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
      >
        Find second jobs
      </button>

      {secondJobLoading ? (
        <div className="flex items-center justify-center gap-2 py-8 text-sm text-gray-600">
          <Loader2 className="h-5 w-5 animate-spin text-teal-600" aria-hidden />
          Finding second jobs for your profile...
        </div>
      ) : null}

      {secondJobError ? (
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-sm text-gray-700">Could not load suggestions. Please try again.</p>
          <button
            type="button"
            onClick={() => void fetchSecondJobs()}
            className="mt-3 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
          >
            Retry
          </button>
        </div>
      ) : null}

      {secondJobResults ? (
        <div className="space-y-4">
          {secondJobResults.jobs.map((job, index) => (
            <div
              key={`${job.title}-${index}`}
              className="rounded-xl border border-gray-200 bg-white p-4"
            >
              {index === 0 ? (
                <span className="mb-2 inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                  Best match
                </span>
              ) : null}
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h4 className="font-semibold text-gray-900">
                  {job.title}{' '}
                  <span className="font-normal text-gray-500">· {job.hourly_range}</span>
                </h4>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                  {formatJobType(job.type)}
                </span>
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                  {job.hours_per_week} hrs/week
                </span>
              </div>
              <p className="mt-2 text-lg font-bold text-teal-600">
                {formatCurrency(job.monthly_est)}/month
              </p>
              <p className="mt-1 text-sm text-gray-600">{job.schedule_fit}</p>
              <div className="mt-3 space-y-2 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                <p>
                  <span className="font-medium">Why it fits:</span> {job.why_it_fits}
                </p>
                <p>
                  <span className="font-medium">Debt impact:</span> {job.debt_impact}
                </p>
                <p>
                  <span className="font-medium">First step:</span> {job.first_step}
                </p>
                <p>
                  <span className="font-medium">Startup cost:</span> {job.startup_cost}
                </p>
              </div>
            </div>
          ))}
          <p className="text-xs text-gray-400">{secondJobResults.disclaimer}</p>
        </div>
      ) : null}
    </div>
  );

  return (
    <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`.trim()}>
      <div className="mb-6 flex gap-2 border-b border-gray-100 pb-3">
        <button
          type="button"
          onClick={() => setSubTab('analyzer')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            subTab === 'analyzer'
              ? 'bg-teal-50 text-teal-800'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          Debt Analyzer
        </button>
        <button
          type="button"
          onClick={() => setSubTab('second-job')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            subTab === 'second-job'
              ? 'bg-teal-50 text-teal-800'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          Second Job Finder
        </button>
      </div>

      {subTab === 'analyzer' ? (
        profileLoading ? (
          <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
            <Loader2 className="h-5 w-5 animate-spin text-teal-600" aria-hidden />
            Loading debt profile…
          </div>
        ) : showResults ? (
          renderResults()
        ) : (
          renderDebtForm()
        )
      ) : (
        renderSecondJobFinder()
      )}

      {showPaymentModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-gray-900">
              How much can you put toward debt each month total?
            </h3>
            <div className="mt-4 space-y-3">
              <NumberField
                label="Monthly payment"
                prefix="$"
                value={monthlyPayment}
                onChange={setMonthlyPayment}
              />
              <NumberField
                label="Extra payment on top of minimums"
                prefix="$"
                value={extraPayment}
                onChange={setExtraPayment}
              />
            </div>
            <div className="mt-6 flex gap-2">
              <button
                type="button"
                onClick={() => setShowPaymentModal(false)}
                className="flex-1 rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={analyzing || !monthlyPayment.trim()}
                onClick={() =>
                  void runCalculate(
                    Number(monthlyPayment),
                    Number(extraPayment || 0),
                  )
                }
                className="flex-1 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
              >
                {analyzing ? 'Running…' : 'Run Analysis →'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default DebtAnalyzerTab;
