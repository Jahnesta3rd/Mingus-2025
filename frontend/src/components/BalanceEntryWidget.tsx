import React, { useCallback, useEffect, useRef, useState } from 'react';

// When integrating on FinancialForecastTab (Prompt 3): enhanced forecast JSON nests
// daily_cashflow under `response.forecast.daily_cashflow`, not at the top level.

const BALANCE_MIN = -1_000_000;
const BALANCE_MAX = 100_000_000;
const STALE_THRESHOLD_DAYS = 30;
const MS_PER_DAY = 86_400_000;

export interface BalanceEntryWidgetProps {
  userEmail: string;
  initialBalance: number;
  lastUpdated: string | null;
  onBalanceSaved: (newBalance: number) => void;
  isLoading?: boolean;
  className?: string;
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(value) ? value : 0);
}

function ageInDaysSince(iso: string): number | null {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return null;
  return Math.floor((Date.now() - t) / MS_PER_DAY);
}

/** Relative label for updates within the last 30 days (quiet style). */
function formatRelativeUpdated(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return 'Updated recently';

  const diffMs = Date.now() - t;
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffDay >= 1) {
    return `Updated ${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
  }
  if (diffHr >= 1) {
    return `Updated ${diffHr} hour${diffHr === 1 ? '' : 's'} ago`;
  }
  if (diffMin >= 1) {
    return `Updated ${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
  }
  return 'Updated just now';
}

function parseBalanceInput(raw: string): { ok: true; value: number } | { ok: false } {
  const cleaned = raw.replace(/[$,]/g, '').trim();
  if (cleaned === '' || cleaned === '-') return { ok: false };
  const n = Number.parseFloat(cleaned);
  if (!Number.isFinite(n)) return { ok: false };
  return { ok: true, value: n };
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export default function BalanceEntryWidget({
  userEmail,
  initialBalance,
  lastUpdated,
  onBalanceSaved,
  isLoading = false,
  className = '',
}: BalanceEntryWidgetProps) {
  void userEmail;

  const [balance, setBalance] = useState(initialBalance);
  const [localLastUpdated, setLocalLastUpdated] = useState(lastUpdated);
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [showSaved, setShowSaved] = useState(false);
  const isEditingRef = useRef(isEditing);
  isEditingRef.current = isEditing;

  useEffect(() => {
    if (isEditingRef.current) return;
    setBalance(initialBalance);
    setLocalLastUpdated(lastUpdated);
  }, [initialBalance, lastUpdated]);

  useEffect(() => {
    if (!showSaved) return undefined;
    const id = window.setTimeout(() => setShowSaved(false), 3000);
    return () => window.clearTimeout(id);
  }, [showSaved]);

  const openEdit = useCallback(() => {
    setValidationError(null);
    setSaveError(null);
    setInputValue(String(balance));
    setIsEditing(true);
  }, [balance]);

  const cancelEdit = useCallback(() => {
    setValidationError(null);
    setSaveError(null);
    setIsEditing(false);
    setBalance(initialBalance);
    setLocalLastUpdated(lastUpdated);
  }, [initialBalance, lastUpdated]);

  const save = useCallback(async () => {
    setValidationError(null);
    setSaveError(null);

    const parsed = parseBalanceInput(inputValue);
    if (!parsed.ok) {
      setValidationError('Please enter a valid number.');
      return;
    }
    if (parsed.value < BALANCE_MIN || parsed.value > BALANCE_MAX) {
      setValidationError('Please enter a balance between -$1M and $100M.');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch('/api/user/balance', {
        method: 'PATCH',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify({ current_balance: parsed.value }),
      });

      if (!res.ok) {
        setSaveError('Unable to save. Please try again.');
        return;
      }

      let updatedAtIso: string | null = new Date().toISOString();
      try {
        const body = (await res.json()) as {
          balance_last_updated?: string | null;
        };
        if (body?.balance_last_updated) {
          updatedAtIso = body.balance_last_updated;
        }
      } catch {
        // keep updatedAtIso as now
      }

      setBalance(parsed.value);
      setLocalLastUpdated(updatedAtIso);
      setIsEditing(false);
      onBalanceSaved(parsed.value);
      setShowSaved(true);
    } catch {
      setSaveError('Unable to save. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [inputValue, onBalanceSaved]);

  const staleNotice = (() => {
    if (localLastUpdated === null) {
      return (
        <p className="mt-1 text-xs text-amber-600">Not set — using default estimate</p>
      );
    }
    const days = ageInDaysSince(localLastUpdated);
    if (days === null) {
      return (
        <p className="mt-1 text-xs text-gray-400">Updated recently</p>
      );
    }
    if (days > STALE_THRESHOLD_DAYS) {
      return (
        <div
          className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700"
          role="status"
        >
          ⚠ Your balance was last updated {days} day{days === 1 ? '' : 's'} ago — tap Update to
          refresh your forecast.
        </div>
      );
    }
    return (
      <p className="mt-1 text-xs text-gray-400">{formatRelativeUpdated(localLastUpdated)}</p>
    );
  })();

  if (isLoading) {
    return (
      <div
        className={`rounded-xl bg-white p-6 shadow-sm ${className}`}
        role="status"
        aria-label="Loading balance"
      >
        <div className="h-10 max-w-md animate-pulse rounded bg-gray-200" />
      </div>
    );
  }

  return (
    <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
      {!isEditing ? (
        <>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-500">Starting Balance</p>
              <p className="text-2xl font-semibold tabular-nums text-gray-900">
                {formatUsd(balance)}
              </p>
              {staleNotice}
            </div>
            <div className="flex flex-col items-stretch sm:items-end">
              <button
                type="button"
                onClick={openEdit}
                aria-expanded={isEditing}
                className="rounded-lg border border-purple-300 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50"
              >
                Update Balance
              </button>
            </div>
          </div>
          {showSaved && (
            <p className="mt-2 text-xs text-green-600">
              ✓ Balance updated — your forecast has been refreshed.
            </p>
          )}
        </>
      ) : (
        <div>
          <label htmlFor="balance-entry-input" className="sr-only">
            Current balance in dollars
          </label>
          <input
            id="balance-entry-input"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            aria-label="Current balance in dollars"
            placeholder="e.g. 3200"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-48 rounded-lg border border-gray-300 px-3 py-2 text-lg focus:ring-2 focus:ring-purple-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-400">
            Enter your approximate checking + savings balance today.
          </p>
          {validationError && (
            <p className="mt-2 text-xs text-red-500" role="alert">
              {validationError}
            </p>
          )}
          {saveError && (
            <p className="mt-2 text-xs text-red-500" role="alert">
              {saveError}
            </p>
          )}
          <div className="mt-4 flex flex-wrap items-center">
            <button
              type="button"
              onClick={() => void save()}
              disabled={saving}
              aria-disabled={saving}
              className="rounded-lg bg-purple-700 px-4 py-2 text-sm font-medium text-white hover:bg-purple-800 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              type="button"
              onClick={cancelEdit}
              disabled={saving}
              className="ml-3 text-sm text-gray-500 underline disabled:cursor-not-allowed disabled:opacity-70"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
