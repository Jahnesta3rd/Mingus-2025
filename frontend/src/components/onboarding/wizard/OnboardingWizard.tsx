import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { commitModule } from '../../../lib/modularOnboarding';
import type { ModuleData, ModuleId } from '../../../types/modularOnboarding';
import { csrfHeaders } from '../../../utils/csrfHeaders';
import { ProgressIndicator } from './ProgressIndicator';
import { STEP_ORDER } from './StepDefinitions';
import { OnboardingSaveAndExit } from '../OnboardingSaveAndExit';

const BASE = '/api/modular-onboarding';
const FINAL_ERROR = "Couldn't complete onboarding. Please try again.";

const STEP_LABEL_BY_ID: Record<ModuleId, string> = Object.fromEntries(
  STEP_ORDER.map((s) => [s.id, s.label])
) as Record<ModuleId, string>;

type FailedField = {
  field_path: string;
  reason: string;
  missing?: string[];
};

function parseStatusComplete(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object') return false;
  const payload = raw as {
    db?: { is_complete?: boolean; completed_modules?: unknown } | null;
    session?: { completed_modules?: unknown };
  };
  if (payload.db?.is_complete === true) return true;
  const fromSession = Array.isArray(payload.session?.completed_modules)
    ? payload.session.completed_modules
    : [];
  const fromDb =
    payload.db && Array.isArray(payload.db.completed_modules) ? payload.db.completed_modules : [];
  const completedSet = new Set<string>(
    [...fromSession, ...fromDb].filter((x): x is string => typeof x === 'string')
  );
  return STEP_ORDER.every((step) => completedSet.has(step.id));
}

function parseStatusModule(raw: unknown): string | null {
  if (!raw || typeof raw !== 'object') return null;
  const payload = raw as {
    session?: { current_module?: unknown };
    db?: { current_module?: unknown } | null;
  };
  const fromSession = payload.session?.current_module;
  if (typeof fromSession === 'string') return fromSession;
  const fromDb = payload.db?.current_module;
  return typeof fromDb === 'string' ? fromDb : null;
}

function moduleIndex(moduleId: string | null): number {
  if (!moduleId) return 0;
  const idx = STEP_ORDER.findIndex((s) => s.id.toLowerCase() === moduleId.toLowerCase());
  return idx >= 0 ? idx : 0;
}

function isModuleId(value: string): value is ModuleId {
  return STEP_ORDER.some((s) => s.id === value);
}

export interface OnboardingWizardProps {
  onComplete?: () => void;
}

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const navigate = useNavigate();

  const finishOnboarding = useCallback(() => {
    // HPRS-13: YES path — queue plan generation if user has home purchase goal
    const housingModule = committedModulesRef.current.housing;
    if (
      housingModule?.has_buy_goal === true &&
      ((housingModule?.target_timeline_months as number | undefined | null) ?? 999) <= 36
    ) {
      fetch('/api/housing/hprs/queue-generation', {
        method: 'POST',
        credentials: 'include',
      }).catch(() => {}); // fire-and-forget — failure is silent
    }

    if (onComplete) {
      onComplete();
      return;
    }
    navigate('/dashboard', { replace: true });
  }, [onComplete, navigate]);
  const { getAccessToken } = useAuth();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [incompleteModules, setIncompleteModules] = useState<ModuleId[]>([]);
  const [initialDataByStep] = useState<Record<string, Record<string, unknown>>>({});
  const committedModulesRef = useRef<Partial<Record<ModuleId, Record<string, unknown>>>>({});

  const currentStep = STEP_ORDER[currentIndex];
  const StepComponent = currentStep.Component;
  const isFirstStep = currentIndex === 0;
  const isLastStep = currentIndex === STEP_ORDER.length - 1;

  const headers = useMemo(() => {
    const token = getAccessToken();
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
      ...csrfHeaders(),
    };
    if (token) {
      h.Authorization = `Bearer ${token}`;
    }
    return h;
  }, [getAccessToken]);

  const fetchStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE}/status`, {
        method: 'GET',
        credentials: 'include',
        headers,
      });
      if (!res.ok) {
        throw new Error('Failed to load onboarding progress');
      }
      const payload = (await res.json()) as unknown;
      if (parseStatusComplete(payload)) {
        finishOnboarding();
        return;
      }
      setCurrentIndex(moduleIndex(parseStatusModule(payload)));
    } catch {
      setCurrentIndex(0);
    } finally {
      setIsLoading(false);
    }
  }, [finishOnboarding, headers]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  const persistSkipAndAdvance = useCallback(async () => {
    const step = STEP_ORDER[currentIndex];
    const res = await fetch(`${BASE}/skip-module`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: JSON.stringify({ module_id: step.id }),
    });
    if (!res.ok) {
      throw new Error('Failed to save step progress');
    }
    const body = (await res.json()) as { next_module?: string | null; all_done?: boolean };
    if (body.next_module) {
      setCurrentIndex(moduleIndex(body.next_module));
      return;
    }
    setCurrentIndex((prev) => Math.min(prev + 1, STEP_ORDER.length - 1));
  }, [currentIndex, headers]);

  const completeFinalStep = useCallback(
    async (data: Record<string, unknown> = {}) => {
      const finalStep = STEP_ORDER[STEP_ORDER.length - 1];
      const res = await fetch(`${BASE}/commit-module`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({ module_id: finalStep.id, data }),
      });

      if (!res.ok) {
        throw new Error(FINAL_ERROR);
      }

      const body = (await res.json()) as {
        ok?: boolean;
        all_done?: boolean;
        failed_fields?: FailedField[];
      };

      const incompleteEntry = body.failed_fields?.find((f) => f.reason === 'incomplete_modules');
      if (body.ok === false && incompleteEntry) {
        const missing = (incompleteEntry.missing ?? []).filter(isModuleId);
        setIncompleteModules(missing);
        setError(null);
        return;
      }

      if (body.failed_fields && body.failed_fields.length > 0) {
        const summary = body.failed_fields
          .map((f) => `${f.field_path}: ${f.reason}`)
          .join('; ');
        throw new Error(
          `Some entries couldn't be saved — ${summary}. Fix and try again, or skip this step.`
        );
      }

      if (body.ok === true && body.all_done === true) {
        setIncompleteModules([]);
        finishOnboarding();
        return;
      }

      if (body.ok === true && body.all_done === false) {
        setIncompleteModules([]);
        setError(
          'You still need to complete every onboarding step before finishing. Use the links below to go back.'
        );
        return;
      }

      setIncompleteModules([]);
      finishOnboarding();
    },
    [finishOnboarding, headers]
  );

  const handleStepSubmit = useCallback(
    async (data: Record<string, unknown>) => {
      if (isSubmitting) return;
      const stepDef = STEP_ORDER[currentIndex];
      if (stepDef.commitOnSubmit && (!data || Object.keys(data).length === 0)) {
        return;
      }
      setIsSubmitting(true);
      setError(null);
      if (!isLastStep) {
        setIncompleteModules([]);
      }
      try {
        if (isLastStep) {
          await completeFinalStep(data);
        } else if (stepDef.commitOnSubmit) {
          const token = getAccessToken();
          if (!token) {
            throw new Error('You must be signed in to continue.');
          }
          const resp = await commitModule(token, stepDef.id, data as ModuleData[ModuleId]);
          committedModulesRef.current = {
            ...committedModulesRef.current,
            [stepDef.id]: data,
          };
          setError(null);
          if (resp.failed_fields && resp.failed_fields.length > 0) {
            const summary = resp.failed_fields
              .map((f) => `${f.field_path}: ${f.reason}`)
              .join('; ');
            throw new Error(`Some entries couldn't be saved — ${summary}.`);
          }
          if (resp.all_done) {
            finishOnboarding();
            return;
          }
          if (resp.next_module) {
            setCurrentIndex(moduleIndex(resp.next_module));
            return;
          }
          setCurrentIndex((prev) => Math.min(prev + 1, STEP_ORDER.length - 1));
        } else {
          await persistSkipAndAdvance();
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : null;
        if (isLastStep) {
          setError(message || FINAL_ERROR);
        } else if (stepDef.commitOnSubmit) {
          setError(message || 'Failed to save step progress');
        } else {
          setError(message || 'Failed to continue');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      completeFinalStep,
      currentIndex,
      finishOnboarding,
      getAccessToken,
      isLastStep,
      isSubmitting,
      persistSkipAndAdvance,
    ]
  );

  const handleSkip = useCallback(async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await persistSkipAndAdvance();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to continue');
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, persistSkipAndAdvance]);

  const goToIncompleteModule = useCallback((moduleId: ModuleId) => {
    setIncompleteModules([]);
    setError(null);
    setCurrentIndex(moduleIndex(moduleId));
  }, []);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4 py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600" />
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col bg-[#F8FAFC]">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 pt-6 sm:flex-row sm:items-start sm:justify-between sm:px-6">
        <div className="min-w-0 flex-1">
          <ProgressIndicator currentIndex={currentIndex} total={STEP_ORDER.length} stepLabel={currentStep.label} />
        </div>
        <div className="flex shrink-0 justify-end sm:pt-0">
          <OnboardingSaveAndExit disabled={isSubmitting} />
        </div>
      </div>

      <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto px-4 py-5 sm:px-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {isLastStep && incompleteModules.length > 0 && (
          <div
            className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            role="alert"
          >
            <p className="font-medium">You still need to complete every step before finishing.</p>
            <ul className="mt-3 space-y-2">
              {incompleteModules.map((moduleId) => {
                const label = STEP_LABEL_BY_ID[moduleId] ?? moduleId;
                return (
                  <li key={moduleId} className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <span>You still need to complete: {label}</span>
                    <button
                      type="button"
                      onClick={() => goToIncompleteModule(moduleId)}
                      className="min-h-11 shrink-0 rounded-lg bg-[#5B2D8E] px-4 py-2 text-sm font-semibold text-white hover:bg-[#4B2474]"
                    >
                      Go to {label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        <StepComponent
          stepLabel={currentStep.label}
          initialData={initialDataByStep[currentStep.id] ?? {}}
          onSubmit={handleStepSubmit}
          onSkip={handleSkip}
          isFirstStep={isFirstStep}
          isLastStep={isLastStep}
        />
      </div>

      <div className="sticky bottom-0 border-t border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 py-4 sm:px-6 min-[640px]:flex-row min-[640px]:justify-between">
          <button
            type="button"
            onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
            disabled={isFirstStep || isSubmitting}
            aria-label={`Back to step ${Math.max(currentIndex, 1)} of ${STEP_ORDER.length}`}
            className="min-h-11 w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 min-[640px]:w-auto"
          >
            Back
          </button>
          {!STEP_ORDER[currentIndex].commitOnSubmit && (
            <button
              type="button"
              onClick={() => void handleStepSubmit({})}
              disabled={isSubmitting}
              aria-label={`Save & Continue to step ${Math.min(currentIndex + 2, STEP_ORDER.length)} of ${STEP_ORDER.length}`}
              className="min-h-11 w-full rounded-lg bg-[#5B2D8E] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#4B2474] disabled:cursor-not-allowed disabled:opacity-60 min-[640px]:w-auto"
            >
              {isSubmitting ? 'Saving...' : 'Save & Continue'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
