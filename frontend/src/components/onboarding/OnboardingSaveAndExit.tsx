import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const EXIT_COPY =
  'Your progress is saved. You can pick up where you left off when you sign back in.';

export type OnboardingSaveAndExitProps = {
  /** e.g. disable while a step save is in flight */
  disabled?: boolean;
};

/**
 * Budget / wizard onboarding: pause and sign out with reassurance copy.
 * Uses the same logout + home redirect pattern as {@link NavigationBar}.
 */
export function OnboardingSaveAndExit({ disabled = false }: OnboardingSaveAndExitProps) {
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleConfirm = useCallback(async () => {
    setSigningOut(true);
    try {
      await Promise.resolve(logout());
      navigate('/', { replace: true });
    } finally {
      setSigningOut(false);
    }
  }, [logout, navigate]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !signingOut) setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, signingOut]);

  return (
    <>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen(true)}
        className="min-h-11 shrink-0 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-sm font-medium text-[#64748B] shadow-sm transition hover:border-[#CBD5E1] hover:bg-[#F8FAFC] hover:text-[#1E293B] disabled:cursor-not-allowed disabled:opacity-50"
      >
        Save & continue later
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-900/50 p-0 sm:items-center sm:p-4"
          role="presentation"
          onClick={() => {
            if (!signingOut) setOpen(false);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-exit-title"
            className="w-full max-w-[380px] rounded-t-2xl border border-[#E2E8F0] bg-white p-5 shadow-xl sm:rounded-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="onboarding-exit-title" className="text-base font-semibold text-[#1E293B]">
              Continue later?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#64748B]">{EXIT_COPY}</p>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
              <button
                type="button"
                disabled={signingOut}
                onClick={() => setOpen(false)}
                className="min-h-11 w-full rounded-lg border border-[#E2E8F0] px-4 py-2.5 text-sm font-medium text-[#64748B] transition hover:bg-[#F8FAFC] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={signingOut}
                onClick={() => void handleConfirm()}
                className="min-h-11 w-full rounded-lg bg-[#5B2D8E] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                {signingOut ? 'Signing out…' : 'Save & sign out'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
