import React, { useCallback, useMemo, useState } from 'react';
import { AlertTriangle, ExternalLink, Loader2, ShieldAlert } from 'lucide-react';
import {
  analyzeBorrowing,
  type BorrowingAnalyzeResponse,
  type BorrowingOption,
} from '../api/borrowingAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface BorrowingScenariosProps {
  defaultAmountNeeded?: number;
  defaultMonthlyIncome?: number;
  defaultSideIncome?: number;
  className?: string;
}

const REASON_OPTIONS = [
  { value: 'bridge_startup', label: 'Bridge startup costs ($2–3k)' },
  { value: 'relationship_unsafe', label: 'Relationship safety emergency' },
  { value: 'emergency_move', label: 'Emergency move' },
  { value: 'general', label: 'General (review carefully)' },
] as const;

function safetyCardClass(level: string, blocked: boolean): string {
  if (blocked) return 'border-red-300 bg-red-50 opacity-80';
  if (level === 'green') return 'border-green-300 bg-green-50/60';
  if (level === 'yellow') return 'border-yellow-300 bg-yellow-50/60';
  return 'border-red-300 bg-red-50/60';
}

function OptionCard({ option }: { option: BorrowingOption }) {
  return (
    <article
      className={`rounded-xl border p-4 ${safetyCardClass(option.safety_level, option.blocked)}`}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="font-semibold text-gray-900">{option.name}</h3>
        {option.recommended ? (
          <span className="rounded-full bg-green-200 px-2 py-0.5 text-xs font-medium text-green-900">
            Recommended
          </span>
        ) : null}
        {option.blocked ? (
          <span className="rounded-full bg-red-200 px-2 py-0.5 text-xs font-medium text-red-900">
            Blocked
          </span>
        ) : null}
      </div>

      {option.monthly_payment > 0 ? (
        <dl className="mb-3 grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-gray-500">Monthly payment</dt>
            <dd className="font-semibold">{formatCurrency(option.monthly_payment)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Term</dt>
            <dd className="font-semibold">{option.term_months} mo</dd>
          </div>
          <div>
            <dt className="text-gray-500">APR</dt>
            <dd className="font-semibold">{option.apr_percent}%</dd>
          </div>
          <div>
            <dt className="text-gray-500">Total repayment</dt>
            <dd className="font-semibold">{formatCurrency(option.total_repayment)}</dd>
          </div>
        </dl>
      ) : (
        <p className="mb-3 text-sm text-gray-600">
          {(option.terms.summary as string) ?? 'No debt required.'}
        </p>
      )}

      <p
        className={`mb-3 text-sm ${
          option.sustainability.sustainable ? 'text-green-800' : 'text-red-800'
        }`}
      >
        Sustainability: {option.sustainability.reasoning}
      </p>

      {option.rule_messages.length > 0 ? (
        <ul className="mb-3 list-disc space-y-1 pl-4 text-xs text-gray-700">
          {option.rule_messages.map((msg) => (
            <li key={msg}>{msg}</li>
          ))}
        </ul>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-xs font-medium uppercase text-green-800">Pros</p>
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
            {option.pros.map((pro) => (
              <li key={pro}>{pro}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase text-red-800">Cons</p>
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
            {option.cons.map((con) => (
              <li key={con}>{con}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

export default function BorrowingScenarios({
  defaultAmountNeeded = 2500,
  defaultMonthlyIncome = 5000,
  defaultSideIncome = 0,
  className = '',
}: BorrowingScenariosProps) {
  const { getAccessToken } = useAuth();
  const [amountNeeded, setAmountNeeded] = useState(defaultAmountNeeded);
  const [monthlyIncome, setMonthlyIncome] = useState(defaultMonthlyIncome);
  const [sideIncome, setSideIncome] = useState(defaultSideIncome);
  const [borrowingReason, setBorrowingReason] = useState('bridge_startup');
  const [relationshipUnsafe, setRelationshipUnsafe] = useState(false);
  const [incomeStable, setIncomeStable] = useState(true);
  const [result, setResult] = useState<BorrowingAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFamilyTemplate, setShowFamilyTemplate] = useState(false);

  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await analyzeBorrowing(
        {
          amountNeeded,
          monthlyIncome,
          sideIncome,
          borrowingReason,
          relationshipUnsafe,
          incomeStable,
        },
        { getAccessToken },
      );
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [
    amountNeeded,
    borrowingReason,
    getAccessToken,
    incomeStable,
    monthlyIncome,
    relationshipUnsafe,
    sideIncome,
  ]);

  const sortedOptions = useMemo(
    () => (result ? [...result.options].sort((a, b) => a.safety_rank - b.safety_rank) : []),
    [result],
  );

  return (
    <section className={`rounded-xl border border-gray-200 bg-gray-50 p-4 sm:p-6 ${className}`}>
      <div className="mb-5 rounded-xl border-2 border-red-500 bg-red-600 p-4 text-white">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-6 w-6 shrink-0" />
          <div>
            <h2 className="text-lg font-bold">Borrowing is a last resort</h2>
            <p className="mt-2 text-sm text-red-50">
              Most users close the gap through side income, expense cuts, and interim housing.
              Only borrow if other paths are exhausted <strong>and</strong> income is stable.
            </p>
            <p className="mt-2 text-xs text-red-100">
              Payday loans, 401(k) withdrawals, and friend loans are never recommended.
            </p>
          </div>
        </div>
      </div>

      <form
        className="mb-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void handleAnalyze();
        }}
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Amount needed</span>
          <input
            type="number"
            min={0}
            step={100}
            value={amountNeeded}
            onChange={(e) => setAmountNeeded(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Monthly income</span>
          <input
            type="number"
            min={0}
            step={100}
            value={monthlyIncome}
            onChange={(e) => setMonthlyIncome(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Side income / mo</span>
          <input
            type="number"
            min={0}
            step={50}
            value={sideIncome}
            onChange={(e) => setSideIncome(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="mb-1 block font-medium text-gray-700">Borrowing reason</span>
          <select
            value={borrowingReason}
            onChange={(e) => {
              const value = e.target.value;
              setBorrowingReason(value);
              setRelationshipUnsafe(value === 'relationship_unsafe');
            }}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          >
            {REASON_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-col justify-end gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={incomeStable}
              onChange={(e) => setIncomeStable(e.target.checked)}
            />
            Income is stable
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={relationshipUnsafe}
              onChange={(e) => setRelationshipUnsafe(e.target.checked)}
            />
            Relationship is unsafe (safety exception)
          </label>
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Analyze borrowing options
          </button>
        </div>
      </form>

      {error ? (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-5">
          <div
            className={`rounded-xl border p-4 ${
              result.allowed
                ? 'border-amber-300 bg-amber-50 text-amber-950'
                : 'border-red-300 bg-red-50 text-red-950'
            }`}
          >
            <p className="font-semibold">
              {result.allowed ? 'Borrowing may be considered' : 'Borrowing not recommended'}
            </p>
            <p className="mt-1 text-sm">{result.recommendation}</p>
            {result.warnings.length > 0 ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {result.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-gray-900">Hard rules checker</h3>
            <ul className="grid gap-2 sm:grid-cols-2">
              {result.hard_rules.map((rule) => (
                <li
                  key={rule}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700"
                >
                  {rule}
                </li>
              ))}
            </ul>
            <div className="mt-3 flex flex-wrap gap-2">
              {result.forbidden_products.map((product) => (
                <span
                  key={product.key}
                  className="rounded-full border border-red-300 bg-red-100 px-3 py-1 text-xs font-medium text-red-900"
                  title={product.reason}
                >
                  ✗ {product.label}
                </span>
              ))}
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {sortedOptions.map((option) => (
              <OptionCard key={option.key} option={option} />
            ))}
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">Scripts & resources</h3>
            <button
              type="button"
              onClick={() => setShowFamilyTemplate((v) => !v)}
              className="text-sm font-medium text-blue-700 hover:underline"
            >
              {showFamilyTemplate ? 'Hide' : 'Show'} family loan template
            </button>
            {showFamilyTemplate ? (
              <pre className="mt-2 overflow-x-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-700 whitespace-pre-wrap">
                {result.resources.family_loan_template}
              </pre>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <a
                href={result.resources.credit_union_locator_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-blue-700 hover:underline"
              >
                Credit union locator
                <ExternalLink className="h-3 w-3" />
              </a>
              <a
                href={result.resources.nfcc_counseling_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-blue-700 hover:underline"
              >
                NFCC credit counseling
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
