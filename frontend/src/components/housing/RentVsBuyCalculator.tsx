import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { csrfHeaders } from '../../utils/csrfHeaders';

export interface GapAnalysisParams {
  home_price: number;
  down_payment_pct: number;
  interest_rate: number;
  loan_term_years: number;
  timeline_months: number;
}

export interface RentVsBuyCalculatorProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
  onPlanRequested: (params: GapAnalysisParams) => void;
  className?: string;
}

interface GapDimension {
  gap: number | null;
  severity: string | null;
}

interface GapAnalysisResult {
  gap_analysis_id: number;
  all_on_track: boolean;
  any_blocked: boolean;
  any_stretched: boolean;
  gaps: {
    income: GapDimension;
    savings_rate: GapDimension;
    down_payment: GapDimension;
    dti: GapDimension;
    credit: GapDimension;
  };
  error?: string;
}

interface CalculatorResults {
  loan: number;
  monthlyPI: number;
  monthlyTax: number;
  monthlyInsurance: number;
  monthlyMaint: number;
  pmi: number;
  totalMonthlyCost: number;
  monthlyRentCost: number;
  breakEvenYear: number | null;
  yearsToCompare: number;
  buyerNetWorth: number;
  renterNetWorth: number;
  netWorthDelta: number;
}

const LOAN_TERM_OPTIONS = [10, 15, 20, 30] as const;

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  return {
    ...csrfHeaders(),
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function formatCurrency(value: number): string {
  return `$${Math.round(Math.abs(value)).toLocaleString()}`;
}

function remainingLoanBalance(
  loan: number,
  monthlyRate: number,
  totalPayments: number,
  paymentsMade: number,
): number {
  if (loan <= 0) return 0;
  if (paymentsMade >= totalPayments) return 0;
  if (monthlyRate === 0) {
    return Math.max(0, loan - (loan / totalPayments) * paymentsMade);
  }
  const powN = Math.pow(1 + monthlyRate, totalPayments);
  const powM = Math.pow(1 + monthlyRate, paymentsMade);
  return loan * (powN - powM) / (powN - 1);
}

function computeCalculatorResults(
  homePrice: number,
  downPaymentPct: number,
  interestRate: number,
  loanTermYears: number,
  monthsToTarget: number,
  monthlyRent: number,
  propertyTaxRate: number,
  maintenanceRate: number,
  homeAppreciation: number,
  investmentReturn: number,
): CalculatorResults | null {
  if (homePrice <= 0 || downPaymentPct <= 0 || downPaymentPct > 100 || interestRate < 0) {
    return null;
  }

  const loan = homePrice * (1 - downPaymentPct / 100);
  const r = interestRate / 100 / 12;
  const n = loanTermYears * 12;

  let monthlyPI: number;
  if (r === 0) {
    monthlyPI = n > 0 ? loan / n : 0;
  } else {
    const factor = Math.pow(1 + r, n);
    monthlyPI = (loan * r * factor) / (factor - 1);
  }

  const monthlyTax = (homePrice * (propertyTaxRate / 100)) / 12;
  const monthlyInsurance = (homePrice * 0.005) / 12;
  const monthlyMaint = (homePrice * (maintenanceRate / 100)) / 12;
  const pmi = downPaymentPct < 20 ? (loan * 0.005) / 12 : 0;
  const totalMonthlyCost = monthlyPI + monthlyTax + monthlyInsurance + monthlyMaint + pmi;
  const monthlyRentCost = monthlyRent + 20;

  const downPaymentAmount = homePrice * (downPaymentPct / 100);
  const closingCostDrag = homePrice * 0.06;
  const growth = 1 + investmentReturn / 100;
  const appreciation = 1 + homeAppreciation / 100;

  let breakEvenYear: number | null = null;
  for (let yr = 1; yr <= 30; yr += 1) {
    const homeValue = homePrice * Math.pow(appreciation, yr);
    const remainingLoan = remainingLoanBalance(loan, r, n, yr * 12);
    const buyerEquity = homeValue - remainingLoan - closingCostDrag;
    const downPaymentInvested = downPaymentAmount * Math.pow(growth, yr);
    const renterNetWorth =
      downPaymentInvested +
      (monthlyRentCost < totalMonthlyCost
        ? (totalMonthlyCost - monthlyRentCost) * 12 * yr * growth
        : 0);

    if (buyerEquity > renterNetWorth) {
      breakEvenYear = yr;
      break;
    }
  }

  const yearsToCompare = Math.max(1, Math.round(monthsToTarget / 12));
  const compareHomeValue = homePrice * Math.pow(appreciation, yearsToCompare);
  const compareRemainingLoan = remainingLoanBalance(loan, r, n, yearsToCompare * 12);
  const buyerNetWorth = compareHomeValue - compareRemainingLoan - closingCostDrag;
  const renterNetWorth =
    downPaymentAmount * Math.pow(growth, yearsToCompare) +
    (monthlyRentCost < totalMonthlyCost
      ? (totalMonthlyCost - monthlyRentCost) * 12 * yearsToCompare * growth
      : 0);
  const netWorthDelta = buyerNetWorth - renterNetWorth;

  return {
    loan,
    monthlyPI,
    monthlyTax,
    monthlyInsurance,
    monthlyMaint,
    pmi,
    totalMonthlyCost,
    monthlyRentCost,
    breakEvenYear,
    yearsToCompare,
    buyerNetWorth,
    renterNetWorth,
    netWorthDelta,
  };
}

function gapSummaryLines(gaps: GapAnalysisResult['gaps']): string[] {
  const entries: { label: string; text: string; priority: number }[] = [];

  const add = (
    label: string,
    gap: number | null | undefined,
    severity: string | null | undefined,
    suffix: string,
    priority: number,
  ) => {
    if (!severity || severity === 'on_track' || gap == null) return;
    entries.push({
      label,
      text: `${label}: ${formatCurrency(gap)}${suffix}`,
      priority,
    });
  };

  add('Income gap', gaps.income.gap, gaps.income.severity, '/month', 1);
  add('Down payment gap', gaps.down_payment.gap, gaps.down_payment.severity, '', 2);
  add('Savings rate gap', gaps.savings_rate.gap, gaps.savings_rate.severity, '/month', 3);
  add('DTI gap', gaps.dti.gap, gaps.dti.severity, '', 4);

  return entries
    .sort((a, b) => a.priority - b.priority)
    .slice(0, 2)
    .map((e) => e.text);
}

function NumberInput({
  label,
  value,
  onChange,
  prefix,
  suffix,
  min,
  max,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  prefix?: string;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-gray-700">{label}</span>
      <div className="flex items-center gap-1">
        {prefix ? <span className="text-sm text-gray-500">{prefix}</span> : null}
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
        />
        {suffix ? <span className="text-sm text-gray-500">{suffix}</span> : null}
      </div>
    </label>
  );
}

function KpiSkeleton() {
  return (
    <div className="min-w-[200px] flex-1 animate-pulse rounded-xl border border-gray-200 bg-white p-4">
      <div className="h-3 w-24 rounded bg-gray-200" />
      <div className="mt-3 h-8 w-32 rounded bg-gray-200" />
      <div className="mt-2 h-3 w-20 rounded bg-gray-100" />
    </div>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string;
  subtitle?: string;
}) {
  return (
    <div className="min-w-[200px] flex-1 rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{title}</p>
      <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
      {subtitle ? <p className="mt-1 text-xs text-gray-500">{subtitle}</p> : null}
    </div>
  );
}

export function RentVsBuyCalculator({
  userEmail: _userEmail,
  userTier,
  onPlanRequested,
  className = '',
}: RentVsBuyCalculatorProps) {
  const [homePrice, setHomePrice] = useState(400000);
  const [downPaymentPct, setDownPaymentPct] = useState(20);
  const [interestRate, setInterestRate] = useState(6.5);
  const [loanTermYears, setLoanTermYears] = useState(30);
  const [monthsToTarget, setMonthsToTarget] = useState(24);
  const [monthlyRent, setMonthlyRent] = useState(2000);
  const [rentInflation, setRentInflation] = useState(3.0);
  const [investmentReturn, setInvestmentReturn] = useState(4.0);
  const [propertyTaxRate, setPropertyTaxRate] = useState(1.1);
  const [maintenanceRate, setMaintenanceRate] = useState(1.0);
  const [homeAppreciation, setHomeAppreciation] = useState(3.0);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [initialLoading, setInitialLoading] = useState(true);
  const [calcError, setCalcError] = useState(false);
  const [calcRetryKey, setCalcRetryKey] = useState(0);
  const [gapResult, setGapResult] = useState<GapAnalysisResult | null>(null);
  const [gapAuthFailed, setGapAuthFailed] = useState(false);

  const isBudget = userTier === 'budget';
  const upgradePlansTo = '/dashboard/upgrade';

  const results = useMemo(() => {
    try {
      return computeCalculatorResults(
        homePrice,
        downPaymentPct,
        interestRate,
        loanTermYears,
        monthsToTarget,
        monthlyRent,
        propertyTaxRate,
        maintenanceRate,
        homeAppreciation,
        investmentReturn,
      );
    } catch {
      return null;
    }
  }, [
    homePrice,
    downPaymentPct,
    interestRate,
    loanTermYears,
    monthsToTarget,
    monthlyRent,
    propertyTaxRate,
    maintenanceRate,
    homeAppreciation,
    investmentReturn,
    calcRetryKey,
  ]);

  useEffect(() => {
    setCalcError(results === null);
    setInitialLoading(false);
  }, [results]);

  const fetchGapAnalysis = useCallback(async () => {
    try {
      const res = await fetch('/api/housing/gap-analysis', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify({
          home_price: homePrice,
          down_payment_pct: downPaymentPct / 100,
          interest_rate: interestRate / 100,
          loan_term_years: loanTermYears,
          timeline_months: monthsToTarget,
        }),
      });

      if (res.status === 401 || res.status === 403) {
        setGapAuthFailed(true);
        setGapResult(null);
        return;
      }

      if (!res.ok) {
        setGapResult(null);
        return;
      }

      const data = (await res.json()) as GapAnalysisResult;
      if (data.error || !data.gap_analysis_id) {
        setGapResult(null);
        return;
      }

      setGapAuthFailed(false);
      setGapResult(data);
    } catch {
      setGapResult(null);
    }
  }, [homePrice, downPaymentPct, interestRate, loanTermYears, monthsToTarget]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchGapAnalysis();
    }, 800);
    return () => window.clearTimeout(timer);
  }, [fetchGapAnalysis]);

  const monthlyDelta = results
    ? results.totalMonthlyCost - results.monthlyRentCost
    : 0;

  const showGapCta =
    !gapAuthFailed &&
    gapResult != null &&
    !gapResult.error &&
    (gapResult.all_on_track || gapResult.any_blocked || gapResult.any_stretched);

  const gapSummaries = gapResult ? gapSummaryLines(gapResult.gaps) : [];

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Rent vs. Buy Calculator</h2>
        <p className="mt-1 text-sm text-gray-600">
          Compare monthly costs and long-term wealth — then see how your profile stacks up.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <NumberInput
            label="Home price"
            prefix="$"
            value={homePrice}
            onChange={setHomePrice}
            min={0}
            step={1000}
          />
          <NumberInput
            label="Down payment"
            suffix="%"
            value={downPaymentPct}
            onChange={setDownPaymentPct}
            min={1}
            max={100}
            step={1}
          />
          <NumberInput
            label="Interest rate"
            suffix="%"
            value={interestRate}
            onChange={setInterestRate}
            min={0}
            max={20}
            step={0.1}
          />
          <label className="block">
            <span className="mb-1 block text-sm text-gray-700">Loan term</span>
            <select
              value={loanTermYears}
              onChange={(e) => setLoanTermYears(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              {LOAN_TERM_OPTIONS.map((term) => (
                <option key={term} value={term}>
                  {term} years
                </option>
              ))}
            </select>
          </label>
          <NumberInput
            label="Months to target purchase"
            value={monthsToTarget}
            onChange={setMonthsToTarget}
            min={12}
            max={360}
            step={1}
          />
          <NumberInput
            label="Monthly rent"
            prefix="$"
            value={monthlyRent}
            onChange={setMonthlyRent}
            min={0}
            step={50}
          />
          <NumberInput
            label="Rent inflation (annual)"
            suffix="%"
            value={rentInflation}
            onChange={setRentInflation}
            min={0}
            max={20}
            step={0.1}
          />
          <NumberInput
            label="Investment return (annual)"
            suffix="%"
            value={investmentReturn}
            onChange={setInvestmentReturn}
            min={0}
            max={20}
            step={0.1}
          />

          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className="flex w-full items-center justify-between rounded-lg border border-gray-100 bg-gray-50/50 px-4 py-3 text-sm font-medium text-gray-800"
          >
            Show advanced
            {showAdvanced ? (
              <ChevronUp className="h-4 w-4 text-gray-500" aria-hidden />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" aria-hidden />
            )}
          </button>

          {showAdvanced ? (
            <div className="space-y-4 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
              <NumberInput
                label="Property tax rate"
                suffix="%"
                value={propertyTaxRate}
                onChange={setPropertyTaxRate}
                min={0}
                max={5}
                step={0.1}
              />
              <NumberInput
                label="Maintenance rate"
                suffix="%"
                value={maintenanceRate}
                onChange={setMaintenanceRate}
                min={0}
                max={5}
                step={0.1}
              />
              <NumberInput
                label="Home appreciation"
                suffix="%"
                value={homeAppreciation}
                onChange={setHomeAppreciation}
                min={0}
                max={20}
                step={0.1}
              />
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          {initialLoading ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              <KpiSkeleton />
              <KpiSkeleton />
              <KpiSkeleton />
            </div>
          ) : calcError ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              {[0, 1, 2].map((idx) => (
                <div
                  key={idx}
                  className="flex-1 rounded-xl border border-gray-200 bg-white p-4 text-center"
                >
                  <p className="text-sm text-gray-600">Unable to load</p>
                  {idx === 0 ? (
                    <button
                      type="button"
                      onClick={() => {
                        setCalcError(false);
                        setCalcRetryKey((k) => k + 1);
                      }}
                      className="mt-2 text-sm font-medium text-teal-600 hover:text-teal-700"
                    >
                      Retry
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          ) : results ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              <KpiCard
                title="Break-even"
                value={
                  results.breakEvenYear != null
                    ? `Year ${results.breakEvenYear}`
                    : '30+ years'
                }
                subtitle="When buying builds more equity than renting"
              />
              <KpiCard
                title="Monthly cost"
                value={
                  monthlyDelta >= 0
                    ? `${formatCurrency(monthlyDelta)}/mo more to buy`
                    : `${formatCurrency(monthlyDelta)}/mo saves renting`
                }
                subtitle="Buy vs. rent (incl. insurance)"
              />
              <KpiCard
                title={`Net worth after ${results.yearsToCompare} years`}
                value={
                  results.netWorthDelta >= 0
                    ? `+${formatCurrency(results.netWorthDelta)} buying`
                    : `${formatCurrency(results.netWorthDelta)} renting`
                }
                subtitle={`Buyer ${formatCurrency(results.buyerNetWorth)} · Renter ${formatCurrency(results.renterNetWorth)}`}
              />
            </div>
          ) : null}

          {results && !calcError ? (
            <div className="overflow-hidden rounded-xl border border-gray-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Buying</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">Monthly</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="px-4 py-2 text-gray-600">P&amp;I</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.monthlyPI)}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-600">Tax</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.monthlyTax)}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-600">Insurance</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.monthlyInsurance)}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-600">Maintenance</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.monthlyMaint)}
                    </td>
                  </tr>
                  {results.pmi > 0 ? (
                    <tr>
                      <td className="px-4 py-2 text-gray-600">PMI</td>
                      <td className="px-4 py-2 text-right text-gray-900">
                        {formatCurrency(results.pmi)}
                      </td>
                    </tr>
                  ) : null}
                  <tr className="bg-gray-50 font-medium">
                    <td className="px-4 py-2 text-gray-900">Total</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.totalMonthlyCost)}
                    </td>
                  </tr>
                </tbody>
              </table>
              <table className="w-full border-t border-gray-200 text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Renting</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">Monthly</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="px-4 py-2 text-gray-600">Rent</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(monthlyRent)}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-600">Renter&apos;s insurance</td>
                    <td className="px-4 py-2 text-right text-gray-900">$20</td>
                  </tr>
                  <tr className="bg-gray-50 font-medium">
                    <td className="px-4 py-2 text-gray-900">Total</td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {formatCurrency(results.monthlyRentCost)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : null}

          {showGapCta && gapResult?.all_on_track ? (
            <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
              ✓ Based on your profile, you&apos;re on track for this purchase.
            </div>
          ) : null}

          {showGapCta &&
          gapResult &&
          (gapResult.any_blocked || gapResult.any_stretched) ? (
            <div className="mt-4 rounded-xl border border-purple-100 bg-purple-50 p-5">
              <h3 className="text-base font-semibold text-gray-900">
                See your personalized homeownership plan
              </h3>
              {gapSummaries.length > 0 ? (
                <p className="mt-2 text-sm text-gray-600">{gapSummaries.join(' · ')}</p>
              ) : null}
              {isBudget ? (
                <Link
                  to={upgradePlansTo}
                  className="mt-4 flex w-full items-center justify-center rounded-full bg-[#7C3AED] px-4 py-3 text-sm font-semibold text-white hover:bg-[#6D28D9]"
                >
                  🔒 Upgrade to unlock your action plan
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={() =>
                    onPlanRequested({
                      home_price: homePrice,
                      down_payment_pct: downPaymentPct / 100,
                      interest_rate: interestRate / 100,
                      loan_term_years: loanTermYears,
                      timeline_months: monthsToTarget,
                    })
                  }
                  className="mt-4 w-full rounded-full bg-[#7C3AED] px-4 py-3 text-sm font-semibold text-white hover:bg-[#6D28D9]"
                >
                  See my action plan →
                </button>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default RentVsBuyCalculator;
