import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SpiritFinance from '../../pages/SpiritFinance';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import {
  CHECKUPS_HUB_PATH,
  authJsonHeaders,
  submitSpiritCalmSupplement,
} from './checkupShared';
import { useAuth } from '../../hooks/useAuth';

type SpiritStreak = {
  last_checkin_date: string | null;
};

/**
 * Thin wrapper around SpiritFinance (#170) — adds dashboard chrome without editing SpiritFinance.tsx.
 * Supplemental grounding capture writes to WeeklyCheckin via POST /api/checkups/spirit-calm.
 */
export function DashSpiritCalmCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [lastCompletedAt, setLastCompletedAt] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [practiceFeltGrounding, setPracticeFeltGrounding] = useState<boolean | null>(null);
  const [meditationMinutes, setMeditationMinutes] = useState<number>(10);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    (async () => {
      setHistoryLoading(true);
      try {
        const res = await fetch('/api/spirit/streak', {
          credentials: 'include',
          headers: authJsonHeaders(),
        });
        if (res.ok) {
          const row = (await res.json()) as SpiritStreak;
          if (!cancelled && row.last_checkin_date) {
            setLastCompletedAt(row.last_checkin_date);
          }
        }
      } catch {
        /* optional */
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const submitSupplement = useCallback(async () => {
    if (practiceFeltGrounding == null) {
      setError('Please indicate whether your practice felt grounding.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await submitSpiritCalmSupplement({
        practice_felt_grounding: practiceFeltGrounding,
        meditation_minutes_total: meditationMinutes,
      });
      setSuccessMessage('Practice logged.');
      window.setTimeout(() => {
        navigate(CHECKUPS_HUB_PATH, { replace: true });
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [meditationMinutes, navigate, practiceFeltGrounding]);

  return (
    <CheckupWrapperShell
      title="Spirit & Calm Check-in"
      score={null}
      lastCompletedAt={lastCompletedAt}
      loading={historyLoading}
      error={error}
      successMessage={successMessage}
    >
      <div className="dash-spirit-wrap space-y-6">
        <div
          className="overflow-hidden rounded-2xl border bg-white shadow-sm"
          style={{ borderColor: 'var(--line)', background: 'var(--whisper-purple)' }}
        >
          <SpiritFinance />
        </div>

        {!successMessage ? (
          <section
            className="dash-checkup-theme space-y-4 rounded-2xl border bg-white p-6 shadow-sm sm:p-8"
            style={{ borderColor: 'var(--line)' }}
            aria-labelledby="spirit-supplement-title"
          >
            <h2 id="spirit-supplement-title" className="font-display text-lg font-semibold">
              After your practice
            </h2>
            <p className="text-sm" style={{ color: 'var(--ink-mid)' }}>
              SpiritFinance does not capture grounding or weekly meditation totals — save these to your wellness
              record.
            </p>

            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">Did this practice feel grounding?</legend>
              <div className="flex gap-3">
                {[true, false].map((val) => (
                  <button
                    key={String(val)}
                    type="button"
                    onClick={() => setPracticeFeltGrounding(val)}
                    className={`min-h-11 flex-1 rounded-xl border px-4 py-3 text-sm font-medium transition ${
                      practiceFeltGrounding === val
                        ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]'
                        : ''
                    }`}
                    style={{ borderColor: practiceFeltGrounding === val ? undefined : 'var(--line)' }}
                  >
                    {val ? 'Yes' : 'No'}
                  </button>
                ))}
              </div>
            </fieldset>

            <div className="space-y-2">
              <label htmlFor="meditation-minutes-total" className="text-sm font-medium">
                Total meditation or calm minutes this week
              </label>
              <input
                id="meditation-minutes-total"
                type="number"
                min={0}
                max={999}
                value={meditationMinutes}
                onChange={(e) => setMeditationMinutes(Math.max(0, Number(e.target.value) || 0))}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </div>

            <button
              type="button"
              onClick={() => void submitSupplement()}
              disabled={busy}
              className="dash-checkup-primary min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"
              style={{ background: 'var(--mingus-purple)' }}
            >
              {busy ? 'Saving…' : 'Save practice notes'}
            </button>
          </section>
        ) : null}
      </div>
    </CheckupWrapperShell>
  );
}

export default DashSpiritCalmCheckup;
