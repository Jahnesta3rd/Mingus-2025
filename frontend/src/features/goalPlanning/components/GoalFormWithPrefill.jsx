import React, { useMemo } from 'react';
import GoalForm from './GoalForm.jsx';
import { useGoalFormPrefill } from '../../../hooks/useGoalFormPrefill.ts';
import styles from './GoalFormWithPrefill.module.css';

/**
 * GoalForm wrapper that applies onboarding-derived defaults and highlights known fields.
 *
 * @param {object} props
 * @param {object} [props.onboardingData]
 * @param {(goal: object) => void} props.onSubmit
 * @param {string[]} [props.goalTypes]
 * @param {boolean} [props.isSubmitting]
 * @param {boolean} [props.autoSubmitLabel]
 * @param {boolean} [props.showAutoSubmit]
 */
export default function GoalFormWithPrefill({
  onboardingData,
  onSubmit,
  goalTypes,
  isSubmitting = false,
  submitSuccess = false,
  showAutoSubmit = false,
  autoSubmitLabel = 'See My Recommendations',
}) {
  const prefill = useGoalFormPrefill(onboardingData);

  const defaultValues = useMemo(() => {
    if (!prefill.defaultValues) {
      return undefined;
    }
    return prefill.defaultValues;
  }, [prefill.defaultValues]);

  const hasOnboardingPrefill = prefill.prefilledFields.length > 0 || prefill.hasGoalInterest;

  return (
    <div className={styles.wrapper}>
      {hasOnboardingPrefill && (
        <div className={styles.banner} role="status">
          <strong>We captured your goal from onboarding.</strong>
          <p>Just refine the details below — fields marked with a checkmark came from your answers.</p>
        </div>
      )}

      <GoalForm
        goalTypes={goalTypes}
        onSubmit={onSubmit}
        defaultValues={defaultValues}
        prefilledFields={prefill.prefilledFields}
        isSubmitting={isSubmitting}
        submitSuccess={submitSuccess}
        submitLabel={showAutoSubmit ? autoSubmitLabel : undefined}
        initialGoalType={prefill.suggestedGoalType ?? undefined}
      />
    </div>
  );
}
