import React, { useCallback, useMemo, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import CashForecastTimeline from './CashForecastTimeline';
import { useCashForecast } from './hooks/useCashForecast';
import styles from './BTSDateSetup.module.css';

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDisplayDate(iso) {
  if (!iso) return '—';
  const d = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function defaultBtsDate() {
  const d = new Date();
  d.setMonth(7, 28); // Aug 28 of current year
  if (d < new Date()) {
    d.setFullYear(d.getFullYear() + 1);
  }
  return d.toISOString().slice(0, 10);
}

/**
 * Back-to-school date + budget setup screen.
 *
 * @param {{
 *   userId?: string,
 *   onContinue?: (setup: object) => void,
 *   initialChildName?: string,
 *   initialChildAge?: number|null,
 *   initialChildGender?: string,
 * }} props
 */
export default function BTSDateSetup({
  userId: userIdProp,
  onContinue,
  initialChildName = '',
  initialChildAge = null,
  initialChildGender = '',
}) {
  const { user, getAccessToken } = useAuth();
  const userId = userIdProp || user?.id || '';

  const [btsDate, setBtsDate] = useState(defaultBtsDate);
  const [childName, setChildName] = useState(initialChildName);
  const [childAge, setChildAge] = useState(
    initialChildAge != null ? String(initialChildAge) : '',
  );
  const [childGender, setChildGender] = useState(initialChildGender);
  const [submittedDate, setSubmittedDate] = useState(null);
  const [formError, setFormError] = useState(null);

  const parsedAge = useMemo(() => {
    if (childAge === '' || childAge == null) return null;
    const n = Number.parseInt(childAge, 10);
    return Number.isFinite(n) ? n : null;
  }, [childAge]);

  const {
    setup,
    timeline,
    loading,
    error,
    tier1Balance,
    shortfall,
    daysUntilSchool,
  } = useCashForecast({
    userId,
    btsDate: submittedDate,
    childName: childName.trim() || undefined,
    childAge: parsedAge,
    childGender: childGender || undefined,
    enabled: Boolean(submittedDate && userId),
    getAccessToken,
  });

  const handleSubmit = useCallback(
    (event) => {
      event.preventDefault();
      setFormError(null);

      if (!userId) {
        setFormError('Sign in to plan your back-to-school budget.');
        return;
      }
      if (!btsDate) {
        setFormError('Choose a back-to-school date.');
        return;
      }

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const chosen = new Date(`${btsDate}T12:00:00`);
      if (chosen < today) {
        setFormError('School start date must be today or later.');
        return;
      }

      setSubmittedDate(btsDate);
    },
    [userId, btsDate],
  );

  const handleContinue = useCallback(() => {
    if (!setup || typeof onContinue !== 'function') return;
    onContinue(setup);
  }, [setup, onContinue]);

  const tier1 = setup?.availableBalances?.tier1;
  const canContinue = Boolean(setup && !loading && !error);

  return (
    <div className={styles.setup}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Back to school</p>
        <h1 className={styles.heading}>When does school start?</h1>
        <p className={styles.subheading}>
          We&apos;ll check how much cash you&apos;ll have two weeks before, so
          essentials come first without stretching payday.
        </p>
      </header>

      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="bts-date">
            Back-to-school date
          </label>
          <input
            id="bts-date"
            className={styles.input}
            type="date"
            value={btsDate}
            min={new Date().toISOString().slice(0, 10)}
            onChange={(e) => setBtsDate(e.target.value)}
            required
          />
        </div>

        <div className={styles.fieldGroup}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="bts-child-name">
              Child&apos;s name <span className={styles.optional}>(optional)</span>
            </label>
            <input
              id="bts-child-name"
              className={styles.input}
              type="text"
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="Emma"
              autoComplete="off"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="bts-child-age">
              Age <span className={styles.optional}>(optional)</span>
            </label>
            <input
              id="bts-child-age"
              className={styles.input}
              type="number"
              min={3}
              max={18}
              value={childAge}
              onChange={(e) => setChildAge(e.target.value)}
              placeholder="8"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="bts-child-gender">
              Shopping for <span className={styles.optional}>(optional)</span>
            </label>
            <select
              id="bts-child-gender"
              className={styles.input}
              value={childGender}
              onChange={(e) => setChildGender(e.target.value)}
            >
              <option value="">Prefer not to say</option>
              <option value="girl">Girl</option>
              <option value="boy">Boy</option>
              <option value="unisex">Unisex / either</option>
            </select>
          </div>
        </div>

        {(formError || error) && (
          <p className={styles.error} role="alert">
            {formError || error}
          </p>
        )}

        <button className={styles.primaryButton} type="submit" disabled={loading}>
          {loading ? 'Checking cash forecast…' : 'Check my budget'}
        </button>
      </form>

      {setup && (
        <section className={styles.results} aria-live="polite">
          <div className={styles.budgetHero}>
            <p className={styles.budgetLabel}>
              Available for Tier 1 essentials
              {tier1?.date ? ` · ${formatDisplayDate(tier1.date)}` : ''}
            </p>
            <p className={styles.budgetAmount}>{formatMoney(tier1Balance)}</p>
            <p className={styles.budgetMeta}>
              {daysUntilSchool != null
                ? `${daysUntilSchool} day${daysUntilSchool === 1 ? '' : 's'} until school`
                : null}
              {setup.estimatedBudget != null
                ? ` · Est. list ~${formatMoney(setup.estimatedBudget)}`
                : null}
            </p>
            {shortfall > 0 ? (
              <p className={styles.shortfall}>
                Shortfall of {formatMoney(shortfall)} vs estimated needs — consider a
                short side gig before Tier 2.
              </p>
            ) : (
              <p className={styles.healthyNote}>
                Forecast looks healthy for first-wave purchases.
              </p>
            )}
          </div>

          <CashForecastTimeline
            timeline={timeline?.timeline || []}
            loading={loading}
          />

          {setup.recommendedSecondJobs?.length > 0 && (
            <section className={styles.jobs}>
              <h3 className={styles.jobsTitle}>Ways to close the gap</h3>
              <ul className={styles.jobList}>
                {setup.recommendedSecondJobs.map((job) => (
                  <li key={job.jobId} className={styles.jobCard}>
                    <div className={styles.jobHeader}>
                      <span className={styles.jobTitle}>{job.title}</span>
                      <span className={styles.jobEarn}>
                        ~{formatMoney(job.potentialEarnings)} by{' '}
                        {formatDisplayDate(job.couldEarnBy)}
                      </span>
                    </div>
                    <p className={styles.jobMeta}>
                      {formatMoney(job.hourlyRate)}/hr · {job.hoursPerWeek} hrs/wk ·
                      startup {job.startupCost === '0' ? 'free' : `$${job.startupCost}`}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setSubmittedDate(null)}
            >
              Change date
            </button>
            <button
              type="button"
              className={styles.primaryButton}
              disabled={!canContinue}
              onClick={handleContinue}
            >
              See product recommendations
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
