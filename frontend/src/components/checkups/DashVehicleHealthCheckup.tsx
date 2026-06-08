import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { VehicleCheckQuizPanel } from '../vehicle-check/VehicleCheckQuizPanel';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitVehicleCheckAnswers } from './checkupShared';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

/**
 * Dashboard-themed Vehicle Health check-in (#170).
 * Uses VehicleCheckQuizPanel (not VehicleCheckPage — that page has no theme prop and bundles lead-gen chrome).
 * Authenticated submit: POST /api/life-ledger/vehicle-check/submit (existing endpoint).
 */
export function DashVehicleHealthCheckup() {
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
        const data = await submitVehicleCheckAnswers(answers);
        await refetch();
        setSuccessMessage(`Vehicle Health updated — ${data.vehicle_score} / 100`);
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

  const lastAt =
    profile?.vehicle_score != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Vehicle Health Check-in"
      score={profile?.vehicle_score ?? null}
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
          <VehicleCheckQuizPanel
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

export default DashVehicleHealthCheckup;
