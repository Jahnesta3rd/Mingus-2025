import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  fetchWisdomCall,
  markWisdomCallRead,
  type WisdomCallPayload,
  type WisdomMilestone,
  type WisdomMilestoneStatus,
} from '../../api/wisdomCallAPI';
import { useAuth } from '../../hooks/useAuth';
import styles from './WisdomCallPage.module.css';

function formatMoney(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `$${Math.round(value).toLocaleString('en-US')}`;
}

function statusBadge(status: WisdomMilestoneStatus): { label: string; className: string } {
  switch (status) {
    case 'on_track':
      return { label: 'On Track ✓', className: styles.badgeOnTrack };
    case 'ahead':
      return { label: 'Ahead 🎯', className: styles.badgeAhead };
    case 'behind':
      return { label: 'Behind ⚠️', className: styles.badgeBehind };
    default:
      return { label: 'Needs data', className: styles.badgeNoData };
  }
}

function progressClass(status: WisdomMilestoneStatus): string {
  switch (status) {
    case 'on_track':
      return styles.progressOnTrack;
    case 'ahead':
      return styles.progressAhead;
    case 'behind':
      return styles.progressBehind;
    default:
      return styles.progressNoData;
  }
}

function MilestoneRow({ milestone }: { milestone: WisdomMilestone }) {
  const badge = statusBadge(milestone.status);
  const pct = Math.max(0, Math.min(100, milestone.progress_pct ?? 0));

  return (
    <article className={styles.milestone}>
      <div className={styles.milestoneHeader}>
        <h3 className={styles.milestoneName}>{milestone.name}</h3>
        <span className={`${styles.badge} ${badge.className}`}>{badge.label}</span>
      </div>

      <p className={styles.amounts}>
        Current: {formatMoney(milestone.current)} / Target: {formatMoney(milestone.target)}
      </p>

      {milestone.projected_date_label ? (
        <p className={styles.dateRow}>
          <span className={styles.dateLabel}>Projected date: </span>
          <span className={styles.dateValue}>{milestone.projected_date_label}</span>
        </p>
      ) : null}

      <div
        className={styles.progressTrack}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-label={`${milestone.name} progress`}
      >
        <div
          className={`${styles.progressFill} ${progressClass(milestone.status)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className={styles.progressMeta}>{pct.toFixed(pct % 1 === 0 ? 0 : 1)}% to target</p>

      {milestone.status === 'behind' && (milestone.shortfall_message || milestone.message) ? (
        <p className={styles.shortfall}>
          {milestone.shortfall_message || milestone.message}
        </p>
      ) : milestone.message ? (
        <p className={styles.progressMeta}>{milestone.message}</p>
      ) : null}
    </article>
  );
}

const WisdomCallPage: React.FC = () => {
  const { week } = useParams<{ week: string }>();
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const [data, setData] = useState<WisdomCallPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copyToast, setCopyToast] = useState(false);
  const trackedRef = useRef<string | null>(null);

  const weekNumber = useMemo(() => {
    const n = Number(week);
    return Number.isFinite(n) ? n : null;
  }, [week]);

  useEffect(() => {
    if (weekNumber == null) {
      setLoading(false);
      setError('Invalid week');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchWisdomCall(weekNumber, { getAccessToken })
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(err instanceof Error ? err.message : 'Failed to load wisdom call');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [weekNumber, getAccessToken]);

  useEffect(() => {
    if (!data || weekNumber == null) return;
    const key = String(weekNumber);
    if (trackedRef.current === key) return;
    trackedRef.current = key;
    markWisdomCallRead(weekNumber, { getAccessToken }).catch(() => {
      /* engagement is best-effort */
    });
  }, [data, weekNumber, getAccessToken]);

  const handleCopy = useCallback(async () => {
    if (!data?.script) return;
    try {
      await navigator.clipboard.writeText(data.script);
      setCopyToast(true);
      window.setTimeout(() => setCopyToast(false), 1800);
    } catch {
      setCopyToast(false);
    }
  }, [data?.script]);

  const handleDownload = useCallback(() => {
    if (!data?.script || weekNumber == null) return;
    const blob = new Blob([data.script], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mingus-wisdom-week-${weekNumber}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }, [data?.script, weekNumber]);

  const handleBack = useCallback(() => {
    navigate('/dashboard/tools');
  }, [navigate]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.state}>
          <p className={styles.stateTitle}>Loading your wisdom call…</p>
          <p>Pulling this week’s script and milestones.</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={styles.page}>
        <div className={styles.state}>
          <p className={styles.stateTitle}>Wisdom call unavailable</p>
          <p>{error || 'No wisdom call found for this week.'}</p>
          <div className={styles.actions} style={{ justifyContent: 'center', marginTop: '1rem' }}>
            <button type="button" className={styles.btnPrimary} onClick={handleBack}>
              Back to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <div className={styles.eyebrow}>Mingus Wisdom · Week {data.week_number}</div>
          <h1 className={styles.title}>Your Wisdom Call</h1>
          <p className={styles.subtitle}>
            A clear read on this week — script, milestones, and what to focus on next.
          </p>
        </div>

        <div className={styles.actions}>
          <button type="button" className={styles.btn} onClick={handleBack}>
            Back
          </button>
          <button type="button" className={styles.btn} onClick={handleCopy}>
            Copy script
          </button>
          <button type="button" className={styles.btnPrimary} onClick={handleDownload}>
            Download
          </button>
          {copyToast ? <span className={styles.toast}>Copied</span> : null}
        </div>
      </header>

      <div className={styles.stack}>
        <section className={styles.scriptCard} aria-label="Wisdom call script">
          <h2 className={styles.sectionTitle}>This week’s script</h2>
          <p className={styles.scriptBody}>{data.script}</p>
        </section>

        <section className={styles.card} aria-label="Financial milestones">
          <h2 className={styles.sectionTitle}>Your Financial Milestones</h2>
          {data.financial_projections?.length || data.milestones?.length ? (
            <div className={styles.milestoneList}>
              {(data.financial_projections?.length ? data.financial_projections : data.milestones).map(
                (milestone) => (
                <MilestoneRow
                  key={`${milestone.name}-${milestone.target_date ?? milestone.projected_date ?? ''}`}
                  milestone={milestone}
                />
              ),
              )}
            </div>
          ) : (
            <p className={styles.emptyMilestones}>
              No active milestones to project yet. Keep checking in — once we have a savings
              rhythm, your dates will show up here.
            </p>
          )}
        </section>

        <section className={styles.audioCard} aria-label="Audio coming soon">
          <h2 className={styles.audioTitle}>Listen (coming soon)</h2>
          <p className={styles.audioHint}>
            Audio wisdom calls arrive in Phase 5. For now, read the script above — same guidance,
            same clarity.
          </p>
          <div className={styles.audioFake} aria-hidden="true">
            Audio player placeholder
          </div>
        </section>
      </div>
    </div>
  );
};

export default WisdomCallPage;
