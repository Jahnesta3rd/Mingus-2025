import { useCallback, useEffect, useState } from 'react';

export interface CashForecastSummary {
  balanceSet: boolean;
  todayBalance: number;
  balance30Day: number;
  netChange: number;
  balanceStatus: 'healthy' | 'warning' | 'danger';
}

export interface UseCashForecastResult {
  data: CashForecastSummary | null;
  loading: boolean;
  error: boolean;
  refetch: () => void;
}

interface DailyCashflowEntry {
  date: string;
  opening_balance: number;
  closing_balance: number;
  balance_status: 'healthy' | 'warning' | 'danger';
}

interface ForecastResponse {
  success: boolean;
  balance_set?: boolean;
  forecast?: {
    daily_cashflow?: DailyCashflowEntry[];
  };
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) {
    (headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return headers;
}

function summarizeFromDaily(
  daily: DailyCashflowEntry[],
  balanceSet: boolean
): CashForecastSummary | null {
  if (daily.length === 0) return null;

  const todayEntry = daily[0];
  const in30Days = new Date();
  in30Days.setDate(in30Days.getDate() + 30);
  const date30Str = in30Days.toISOString().slice(0, 10);
  const entry30 =
    daily.find((e) => e.date === date30Str) ?? daily[29] ?? daily[daily.length - 1];

  const todayBalance = todayEntry.opening_balance;
  const balance30Day = entry30.closing_balance;
  const status = todayEntry.balance_status;
  const balanceStatus: CashForecastSummary['balanceStatus'] =
    status === 'healthy' || status === 'warning' || status === 'danger'
      ? status
      : 'healthy';

  return {
    balanceSet,
    todayBalance,
    balance30Day,
    netChange: balance30Day - todayBalance,
    balanceStatus,
  };
}

async function fetchCashForecast(userEmail: string): Promise<CashForecastSummary | null> {
  const encoded = encodeURIComponent(userEmail);
  const primaryUrl = `/api/cash-flow/enhanced-forecast/${encoded}?months=3`;
  const fallbackUrl = `/api/cash-flow/backward-compatibility/${encoded}?months=3`;
  const headers = buildAuthHeaders();

  let res = await fetch(primaryUrl, { credentials: 'include', headers });
  if (!res.ok) {
    res = await fetch(fallbackUrl, { credentials: 'include', headers });
  }
  if (!res.ok) {
    throw new Error('Failed to load cash forecast');
  }

  const json = (await res.json()) as ForecastResponse;
  const daily = json.forecast?.daily_cashflow ?? [];
  const balanceSet = json.balance_set ?? true;
  return summarizeFromDaily(daily, balanceSet);
}

export function useCashForecast(userEmail: string): UseCashForecastResult {
  const [data, setData] = useState<CashForecastSummary | null>(null);
  const [loading, setLoading] = useState(Boolean(userEmail.trim()));
  const [error, setError] = useState(false);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    setFetchKey((k) => k + 1);
  }, []);

  useEffect(() => {
    const email = userEmail.trim();
    if (!email) {
      setData(null);
      setLoading(false);
      setError(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(false);

    fetchCashForecast(email)
      .then((summary) => {
        if (cancelled) return;
        setData(summary);
        setError(false);
      })
      .catch(() => {
        if (cancelled) return;
        setData(null);
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [userEmail, fetchKey]);

  return { data, loading, error, refetch };
}
