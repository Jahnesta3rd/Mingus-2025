import React, { useState } from 'react';
import styles from './JobPicker.module.css';

const DEFAULT_JOBS = [
  { id: 'doordash', title: 'DoorDash' },
  { id: 'instacart', title: 'Instacart' },
  { id: 'rideshare', title: 'Rideshare' },
  { id: 'tutoring', title: 'After-School Tutor' },
  { id: 'uber', title: 'Uber Eats' },
  { id: 'taskrabbit', title: 'TaskRabbit' },
  { id: 'other', title: 'Other side job' },
];

/**
 * Modal to pick a side job + target earnings for Tier 2.
 */
export default function JobPickerModal({
  tier2BaseBudget,
  onSelect,
  onClose,
  submitting = false,
  jobs = DEFAULT_JOBS,
}) {
  const [selectedJob, setSelectedJob] = useState(null);
  const [targetEarnings, setTargetEarnings] = useState('');
  const [error, setError] = useState(null);

  const base = Number(tier2BaseBudget) || 0;
  const targetNum = Number(targetEarnings);
  const projected =
    Number.isFinite(targetNum) && targetNum > 0 ? base + targetNum : base;

  const handleSelect = () => {
    if (!selectedJob || !targetEarnings) {
      setError('Please select a job and enter target earnings');
      return;
    }
    const target = parseFloat(targetEarnings);
    if (!Number.isFinite(target) || target <= 0) {
      setError('Target earnings must be a positive number');
      return;
    }
    setError(null);
    onSelect({
      jobId: selectedJob.id,
      jobTitle: selectedJob.title,
      targetEarnings: target,
    });
  };

  return (
    <div className={styles.overlay} onClick={onClose} role="presentation">
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="job-picker-title"
      >
        <h2 id="job-picker-title">Add a side job for Tier 2</h2>
        <p className={styles.description}>
          Link a side job so earnings can boost your Tier 2 budget. Progress
          updates automatically as DF1 records income.
        </p>

        <div className={styles.section}>
          <p className={styles.label}>Which side job?</p>
          <div className={styles.jobOptions}>
            {jobs.map((job) => (
              <button
                key={job.id}
                type="button"
                className={`${styles.jobOption} ${
                  selectedJob?.id === job.id ? styles.selected : ''
                }`}
                onClick={() => {
                  setSelectedJob(job);
                  setError(null);
                }}
              >
                {job.title}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <label className={styles.label} htmlFor="bts-target-earnings">
            Earnings target for Tier 2
          </label>
          <input
            id="bts-target-earnings"
            type="number"
            placeholder="e.g. 300"
            value={targetEarnings}
            onChange={(e) => {
              setTargetEarnings(e.target.value);
              setError(null);
            }}
            className={styles.input}
            min="1"
            step="10"
          />
          <p className={styles.note}>
            Tier 2 base budget: ${base.toFixed(2)}
            <br />
            Projected total if you hit the target: ${projected.toFixed(2)}
          </p>
        </div>

        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}

        <div className={styles.actions}>
          <button
            type="button"
            onClick={onClose}
            className={styles.secondaryButton}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSelect}
            className={styles.primaryButton}
            disabled={submitting}
          >
            {submitting ? 'Linking…' : 'Link job'}
          </button>
        </div>
      </div>
    </div>
  );
}
