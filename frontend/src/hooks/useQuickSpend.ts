import { useCallback, useMemo, useState } from "react";
import { useAuth } from "./useAuth";
import { csrfHeaders } from "../utils/csrfHeaders";

export interface QuickSpendPayload {
  amount: number;
  spend_vibe: string;
  vibe_signal: string;
  merchant_id?: string;
  merchant_name?: string;
  merchant_group?: string;
  date?: string;
}

export interface QuickSpendEntry {
  id: number;
  date: string;
  amount: number;
  spend_vibe: string;
  vibe_signal: string;
  merchant_name: string | null;
  merchant_group: string | null;
  merchant_id: string | null;
  logged_at: string;
}

export interface TodayLog {
  date: string;
  entries: QuickSpendEntry[];
  total: number;
  count: number;
}

export interface QuickSpendSummary {
  period_days: number;
  start_date: string;
  end_date: string;
  total: number;
  by_signal: Record<string, number>;
  by_vibe: Record<string, number>;
}

export function useQuickSpend() {
  const { getAccessToken } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [todayLog, setTodayLog] = useState<TodayLog | null>(null);
  const [loadingToday, setLoadingToday] = useState(false);

  const authHeaders = useMemo(() => {
    const token = getAccessToken();
    return {
      "Content-Type": "application/json",
      ...csrfHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, [getAccessToken]);

  const logSpend = useCallback(
    async (payload: QuickSpendPayload): Promise<QuickSpendEntry> => {
      setSaving(true);
      setSaveError(null);
      try {
        const res = await fetch("/api/expenses/quick-log", {
          method: "POST",
          credentials: "include",
          headers: authHeaders,
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error((err as { error?: string }).error ?? `HTTP ${res.status}`);
        }
        const entry: QuickSpendEntry = await res.json();
        setTodayLog((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            entries: [entry, ...prev.entries],
            total: prev.total + entry.amount,
            count: prev.count + 1,
          };
        });
        return entry;
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : "Failed to save";
        setSaveError(message);
        throw e;
      } finally {
        setSaving(false);
      }
    },
    [authHeaders]
  );

  const fetchToday = useCallback(async () => {
    setLoadingToday(true);
    try {
      const res = await fetch("/api/expenses/quick-log/today", {
        credentials: "include",
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: TodayLog = await res.json();
      setTodayLog(data);
    } catch (e) {
      console.warn("useQuickSpend fetchToday failed:", e);
    } finally {
      setLoadingToday(false);
    }
  }, [authHeaders]);

  const fetchSummary = useCallback(
    async (days = 30): Promise<QuickSpendSummary | null> => {
      try {
        const res = await fetch(
          `/api/expenses/quick-log/summary?days=${days}`,
          { credentials: "include", headers: authHeaders }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      } catch (e) {
        console.warn("useQuickSpend fetchSummary failed:", e);
        return null;
      }
    },
    [authHeaders]
  );

  return {
    logSpend,
    fetchToday,
    fetchSummary,
    saving,
    saveError,
    todayLog,
    loadingToday,
  };
}
