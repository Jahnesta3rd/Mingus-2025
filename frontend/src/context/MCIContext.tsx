import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import type { MCISnapshot, MCIContextValue } from "../types/mci";

export const MCIContext = createContext<MCIContextValue>({
  snapshot: null,
  loading: false,
  error: null,
  refresh: () => undefined,
});

const API_URL = "/api/mci/snapshot";

export const MCIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [snapshot, setSnapshot] = useState<MCISnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSnapshot = useCallback(
    async (bypassBrowserCache: boolean) => {
      try {
        setLoading(true);
        setError(null);

        const tokenFromMingus = localStorage.getItem("mingus_token");
        const tokenFromAuth = localStorage.getItem("auth_token");
        const token = tokenFromMingus ?? tokenFromAuth ?? "";

        const url = `${API_URL}${bypassBrowserCache ? `?t=${Date.now()}` : ""}`;

        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch MCI snapshot");
        }

        const data = await response.json();
        const resolvedSnapshot = (data?.data ?? data) as MCISnapshot;
        setSnapshot(resolvedSnapshot);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load MCI snapshot";
        setError(errorMessage);
        setSnapshot(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const refresh = useCallback(() => {
    fetchSnapshot(true);
  }, [fetchSnapshot]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      setSnapshot(null);
      setLoading(false);
      setError(null);
      return;
    }
    // fetch once when we transition into an authenticated state
    fetchSnapshot(false);
  }, [authLoading, isAuthenticated, fetchSnapshot]);

  const value: MCIContextValue = useMemo(
    () => ({
      snapshot,
      loading,
      error,
      refresh,
    }),
    [snapshot, loading, error, refresh]
  );

  return <MCIContext.Provider value={value}>{children}</MCIContext.Provider>;
};

export const useMCI = () => useContext(MCIContext);

