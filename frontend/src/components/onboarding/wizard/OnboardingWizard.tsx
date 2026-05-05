import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { csrfHeaders } from '../../../utils/csrfHeaders';
import { ProgressIndicator } from './ProgressIndicator';
import { STEP_ORDER } from './StepDefinitions';

const BASE = '/api/modular-onboarding';
const FINAL_ERROR = "Couldn't complete onboarding. Please try again.";

function parseStatusComplete(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object') return false;
  const payload = raw as {
    db?: { is_complete?: boolean } | null;
    session?: {
      completed_modules?: unknown;
      skipped_modules?: unknown;
    };
  };
  if (payload.db?.is_complete === true) return true;
  const completed = Array.isArray(payload.session?.completed_modules)
    ? payload.session?.completed_modules
    : [];
  const skipped = Array.isArray(payload.session?.skipped_modules)
    ? payload.session?.skipped_modules
    : [];
  const seen = new Set<string>([...completed, ...skipped].filter((x): x is string => typeof x === 'string'));
  return STEP_ORDER.every((step) => seen.has(step.id));
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

export default function OnboardingWizard() {
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialDataByStep] = useState<Record<string, Record<string, unknown>>>({});

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
        navigate('/dashboard', { replace: true });
        return;
      }
      setCurrentIndex(moduleIndex(parseStatusModule(payload)));
    } catch {
      setCurrentIndex(0);
    } finally {
      setIsLoading(false);
    }
  }, [headers, navigate]);

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
    if (body.all_done) {
      navigate('/dashboard', { replace: true });
      return;
    }
    if (body.next_module) {
      setCurrentIndex(moduleIndex(body.next_module));
      return;
    }
    setCurrentIndex((prev) => Math.min(prev + 1, STEP_ORDER.length - 1));
  }, [currentIndex, headers, navigate]);

  const completeFinalStep = useCallback(async () => {
    const finalStep = STEP_ORDER[STEP_ORDER.length - 1];
    const res = await fetch(`${BASE}/commit-module`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: JSON.stringify({ module_id: finalStep.id, data: {} }),
    });
    if (!res.ok) {
      throw new Error(FINAL_ERROR);
    }
    navigate('/dashboard', { replace: true });
  }, [headers, navigate]);

  const handleStepSubmit = useCallback(
    async (_data: Record<string, unknown>) => {
      if (isSubmitting) return;
      setIsSubmitting(true);
      setError(null);
      try {
        if (isLastStep) {
          await completeFinalStep();
        } else {
          await persistSkipAndAdvance();
        }
      } catch (err) {
        if (isLastStep) {
          setError(FINAL_ERROR);
        } else {
          setError(err instanceof Error ? err.message : 'Failed to continue');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [completeFinalStep, isLastStep, isSubmitting, persistSkipAndAdvance]
  );

  const handleSkip = useCallback(() => {
    void handleStepSubmit({});
  }, [handleStepSubmit]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4 py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600" />
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col bg-[#F8FAFC]">
      <div className="mx-auto w-full max-w-4xl px-4 pt-6 sm:px-6">
        <ProgressIndicator currentIndex={currentIndex} total={STEP_ORDER.length} stepLabel={currentStep.label} />
      </div>

      <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto px-4 py-5 sm:px-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
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
          <button
            type="button"
            onClick={() => void handleStepSubmit({})}
            disabled={isSubmitting}
            aria-label={`Save & Continue to step ${Math.min(currentIndex + 2, STEP_ORDER.length)} of ${STEP_ORDER.length}`}
            className="min-h-11 w-full rounded-lg bg-[#5B2D8E] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#4B2474] disabled:cursor-not-allowed disabled:opacity-60 min-[640px]:w-auto"
          >
            {isSubmitting ? 'Saving...' : 'Save & Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}
