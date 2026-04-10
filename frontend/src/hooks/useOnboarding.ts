import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

export const ONBOARDING_STEP_KEYS = ['personal', 'income', 'expenses', 'position', 'goals'] as const;

function buildHeaders(getAccessToken: () => string | null, json = false): HeadersInit {
  const h: Record<string, string> = {
    ...csrfHeaders(),
  };
  if (json) {
    h['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

function firstIncompleteStep(completed: string[]): number {
  for (let i = 0; i < ONBOARDING_STEP_KEYS.length; i++) {
    if (!completed.includes(ONBOARDING_STEP_KEYS[i])) {
      return i + 1;
    }
  }
  return 5;
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

export interface SavePersonalPayload {
  personalInfo: Record<string, unknown>;
}

export interface SaveIncomePayload {
  sources: Array<{
    source_name: string;
    amount: number;
    frequency: string;
    pay_day?: number | null;
  }>;
}

export interface SaveExpensesPayload {
  expenses: Array<{
    name: string;
    amount: number;
    category: string;
    frequency: string;
    due_day?: number | null;
  }>;
}

export interface SavePositionPayload {
  emergency_fund?: number;
  credit_score?: number | null;
  total_debt?: number | null;
  savings_balance?: number | null;
}

export interface SaveGoalsPayload {
  /** Object or JSON string (string is parsed before merge) */
  goals: Record<string, unknown> | string;
}

interface ProfileBundle {
  personalInfo: Record<string, unknown>;
  financialInfo: Record<string, unknown>;
  monthlyExpenses: Record<string, unknown>;
  importantDates: Record<string, unknown>;
  healthWellness: Record<string, unknown>;
  goals: Record<string, unknown>;
  firstNameTop: string;
}

const emptyBundle = (): ProfileBundle => ({
  personalInfo: {},
  financialInfo: {},
  monthlyExpenses: {},
  importantDates: {},
  healthWellness: {},
  goals: {},
  firstNameTop: '',
});

export function useOnboarding() {
  const { user, getAccessToken } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [stepsCompleted, setStepsCompleted] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfileBundle = useCallback(async (): Promise<ProfileBundle> => {
    const email = user?.email;
    if (!email) {
      return emptyBundle();
    }
    const res = await fetch(`/api/profile/${encodeURIComponent(email)}`, {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    if (!res.ok) {
      return emptyBundle();
    }
    const j = (await res.json()) as { profile?: Record<string, unknown> };
    const p = j.profile;
    if (!p) {
      return emptyBundle();
    }
    return {
      personalInfo: (p.personal_info as Record<string, unknown>) || {},
      financialInfo: (p.financial_info as Record<string, unknown>) || {},
      monthlyExpenses: (p.monthly_expenses as Record<string, unknown>) || {},
      importantDates: (p.important_dates as Record<string, unknown>) || {},
      healthWellness: (p.health_wellness as Record<string, unknown>) || {},
      goals: (p.goals as Record<string, unknown>) || {},
      firstNameTop: String(p.first_name || ''),
    };
  }, [user?.email, getAccessToken]);

  const refreshSetupStatus = useCallback(async () => {
    const res = await fetch('/api/profile/setup-status', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    if (!res.ok) {
      return;
    }
    const data = (await res.json()) as {
      steps_completed?: string[];
      data?: { steps_completed?: string[] };
    };
    const done = data.steps_completed ?? data.data?.steps_completed ?? [];
    setStepsCompleted(done);
    setCurrentStep(firstIncompleteStep(done));
  }, [getAccessToken]);

  useEffect(() => {
    if (!user?.email) {
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/profile/setup-status', {
          method: 'GET',
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
        });
        if (!res.ok) {
          throw new Error(await readErrorMessage(res));
        }
        const data = (await res.json()) as {
          steps_completed?: string[];
          data?: { steps_completed?: string[] };
        };
        const done = data.steps_completed ?? data.data?.steps_completed ?? [];
        if (!cancelled) {
          setStepsCompleted(done);
          setCurrentStep(firstIncompleteStep(done));
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load setup status');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user?.email, getAccessToken]);

  const goToStep = useCallback((n: number) => {
    if (n >= 1 && n <= 5) {
      setCurrentStep(n);
    }
  }, []);

  const skipStep = useCallback(() => {
    setCurrentStep((s) => Math.min(s + 1, 5));
  }, []);

  const savePersonal = useCallback(
    async (payload: SavePersonalPayload): Promise<boolean> => {
      const email = user?.email;
      if (!email) {
        setError('Not signed in');
        return false;
      }
      setIsSaving(true);
      setError(null);
      try {
        const bundle = await fetchProfileBundle();
        const mergedPersonal = { ...bundle.personalInfo, ...payload.personalInfo };
        const firstName =
          String(mergedPersonal.firstName || mergedPersonal.first_name || bundle.firstNameTop || '');
        const body = {
          email,
          firstName,
          personalInfo: mergedPersonal,
          financialInfo: bundle.financialInfo,
          monthlyExpenses: bundle.monthlyExpenses,
          importantDates: bundle.importantDates,
          healthWellness: bundle.healthWellness,
          goals: bundle.goals,
        };
        const res = await fetch('/api/profile', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify(body),
        });
        if (res.status !== 200 && res.status !== 201) {
          setError(await readErrorMessage(res));
          return false;
        }
        await refreshSetupStatus();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Save failed');
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [user?.email, getAccessToken, fetchProfileBundle, refreshSetupStatus]
  );

  const saveIncome = useCallback(
    async (payload: SaveIncomePayload): Promise<boolean> => {
      setIsSaving(true);
      setError(null);
      try {
        const res = await fetch('/api/financial-setup/income', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify({ sources: payload.sources }),
        });
        if (res.status !== 200 && res.status !== 201) {
          setError(await readErrorMessage(res));
          return false;
        }
        await refreshSetupStatus();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Save failed');
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [getAccessToken, refreshSetupStatus]
  );

  const saveExpenses = useCallback(
    async (payload: SaveExpensesPayload): Promise<boolean> => {
      setIsSaving(true);
      setError(null);
      try {
        const res = await fetch('/api/financial-setup/expenses', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify({ expenses: payload.expenses }),
        });
        if (res.status !== 200 && res.status !== 201) {
          setError(await readErrorMessage(res));
          return false;
        }
        await refreshSetupStatus();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Save failed');
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [getAccessToken, refreshSetupStatus]
  );

  const savePosition = useCallback(
    async (payload: SavePositionPayload): Promise<boolean> => {
      setIsSaving(true);
      setError(null);
      try {
        const res = await fetch('/api/financial-setup/position', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify(payload),
        });
        if (res.status !== 200 && res.status !== 201) {
          setError(await readErrorMessage(res));
          return false;
        }
        await refreshSetupStatus();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Save failed');
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [getAccessToken, refreshSetupStatus]
  );

  const saveGoals = useCallback(
    async (payload: SaveGoalsPayload): Promise<boolean> => {
      const email = user?.email;
      if (!email) {
        setError('Not signed in');
        return false;
      }
      setIsSaving(true);
      setError(null);
      try {
        const bundle = await fetchProfileBundle();
        let goalsPatch: Record<string, unknown>;
        if (typeof payload.goals === 'string') {
          goalsPatch = JSON.parse(payload.goals) as Record<string, unknown>;
        } else {
          goalsPatch = payload.goals;
        }
        const mergedGoals = { ...bundle.goals, ...goalsPatch };
        const mergedPersonal = { ...bundle.personalInfo };
        const firstName =
          String(mergedPersonal.firstName || mergedPersonal.first_name || bundle.firstNameTop || '');
        const body = {
          email,
          firstName,
          personalInfo: mergedPersonal,
          financialInfo: bundle.financialInfo,
          monthlyExpenses: bundle.monthlyExpenses,
          importantDates: bundle.importantDates,
          healthWellness: bundle.healthWellness,
          goals: mergedGoals,
        };
        const res = await fetch('/api/profile', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify(body),
        });
        if (res.status !== 200 && res.status !== 201) {
          setError(await readErrorMessage(res));
          return false;
        }
        await refreshSetupStatus();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Save failed');
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [user?.email, getAccessToken, fetchProfileBundle, refreshSetupStatus]
  );

  return {
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
  };
}
