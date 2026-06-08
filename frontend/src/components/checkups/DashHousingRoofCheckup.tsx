import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoofCheckQuizPanel } from '../roof-check/RoofCheckQuizPanel';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitRoofCheckAnswers } from './checkupShared';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

/**
 * Dashboard-themed Housing & Roof check-in (#170).
 * Uses RoofCheckQuizPanel (not RoofCheckPage — no theme prop; lead-gen chrome baked in).
 * Authenticated submit: POST /api/life-ledger/roof-check/submit (existing endpoint).
 */
export function DashHousingRoofCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const [panelKey, setPanelKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const onQuizComplete = useCallback(
    async (answers: Record<string, number>) => {
      setBusy(true);
      setError(null);
      try {
        const data = await submitRoofCheckAnswers(answers);
        await refetch();
        setSuccessMessage(`Roof score updated — ${data.roof_score} / 100`);
        window.setTimeout(() => {
          navigate(CHECKUPS_HUB_PATH, { replace: true });
        }, 2000);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Submit failed');
        setPanelKey((k) => k + 1);
      } finally {
        setBusy(false);
      }
    },
    [navigate, refetch]
  );

  const lastAt = profile?.roof_score != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Housing & Roof Check-in"
      score={profile?.roof_score ?? null}
      lastCompletedAt={lastAt}
      loading={profileLoading}
      error={error}
      successMessage={successMessage}
    >
      {!successMessage ? (
        <div
          className="dash-checkup-theme rounded-2xl border bg-white p-6 shadow-sm sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <RoofCheckQuizPanel
            key={panelKey}
            onComplete={onQuizComplete}
            onError={setError}
            busy={busy || profileLoading}
          />
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashHousingRoofCheckup;
