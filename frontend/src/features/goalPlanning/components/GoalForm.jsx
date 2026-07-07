import React, { useEffect, useMemo, useState } from 'react';
import {
  Baby,
  Briefcase,
  Building2,
  Car,
  Home,
  Loader2,
} from 'lucide-react';
import { getGoalTypeOptions, loadGoalDefinition } from '../goalDefinitions/index.ts';
import {
  buildInitialFormValues,
  formatCurrencyInput,
  generateGoalSummary,
  parseCurrencyInput,
  submitGoal,
  validateForm,
} from '../utils/goalFormUtils.js';
import styles from './GoalForm.module.css';

const ICON_MAP = {
  home: Home,
  car: Car,
  building: Building2,
  baby: Baby,
  briefcase: Briefcase,
};

/**
 * @param {object} props
 * @param {(goal: object) => void} props.onSubmit
 * @param {string[]} [props.goalTypes]
 * @param {object} [props.defaultValues]
 * @param {boolean} [props.isSubmitting]
 * @param {boolean} [props.submitSuccess]
 */
export default function GoalForm({
  onSubmit,
  goalTypes,
  defaultValues,
  prefilledFields = [],
  initialGoalType,
  isSubmitting = false,
  submitSuccess = false,
  submitLabel,
}) {
  const goalOptions = useMemo(() => getGoalTypeOptions(goalTypes), [goalTypes]);
  const prefilledSet = useMemo(() => new Set(prefilledFields), [prefilledFields]);
  const [goalType, setGoalType] = useState(initialGoalType ?? defaultValues?.type ?? '');
  const [formValues, setFormValues] = useState({});
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [formError, setFormError] = useState('');

  const definition = loadGoalDefinition(goalType);
  const validation = useMemo(
    () => validateForm(definition, formValues),
    [definition, formValues],
  );
  const summary = goalType ? generateGoalSummary(goalType, formValues) : '';
  const TypeIcon = definition ? ICON_MAP[definition.icon] ?? Home : Home;

  useEffect(() => {
    if (initialGoalType && !goalType) {
      setGoalType(initialGoalType);
    }
  }, [initialGoalType, goalType]);

  useEffect(() => {
    if (!goalType) {
      setFormValues({});
      setErrors({});
      setTouched({});
      return;
    }
    const nextDefinition = loadGoalDefinition(goalType);
    setFormValues(buildInitialFormValues(nextDefinition, defaultValues?.type === goalType ? defaultValues : null));
    setErrors({});
    setTouched({});
    setFormError('');
  }, [goalType, defaultValues]);

  const handleGoalTypeChange = (event) => {
    setGoalType(event.target.value);
    setFormError('');
  };

  const handleFieldChange = (field, value) => {
    setFormValues((prev) => ({
      ...prev,
      [field.name]: value,
    }));
    setTouched((prev) => ({ ...prev, [field.name]: true }));
  };

  const handleCurrencyChange = (field, rawValue) => {
    const formatted = formatCurrencyInput(parseCurrencyInput(rawValue) ?? rawValue);
    handleFieldChange(field, formatted);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setFormError('');

    const nextValidation = validateForm(definition, formValues);
    setErrors(nextValidation.errors);
    setTouched(Object.fromEntries((definition?.fields ?? []).map((field) => [field.name, true])));

    if (!nextValidation.isValid) {
      setFormError('Please fix the highlighted fields before continuing.');
      return;
    }

    const goal = submitGoal(goalType, formValues);
    if (!goal) {
      setFormError('Unable to build goal from form values.');
      return;
    }

    onSubmit(goal);
  };

  const renderFormField = (field) => {
    const fieldError = touched[field.name] ? errors[field.name] : '';
    const inputClassName = `${styles.input}${fieldError ? ` ${styles.inputError}` : ''}`;
    const fromOnboarding = prefilledSet.has(field.name);

    const onboardingNote = fromOnboarding ? (
      <p className={styles.onboardingKnown}>✓ We know this from onboarding</p>
    ) : null;

    if (field.type === 'percent') {
      const value = Number(formValues[field.name] ?? field.default ?? 0);
      return (
        <div key={field.name} className={styles.field}>
          <label className={styles.label} htmlFor={field.name}>{field.label}</label>
          <div className={styles.percentRow}>
            <input
              id={field.name}
              type="range"
              className={styles.slider}
              min={field.min ?? 0}
              max={field.max ?? 100}
              step={1}
              value={value}
              onChange={(event) => handleFieldChange(field, Number(event.target.value))}
            />
            <span className={styles.percentValue}>{value}%</span>
          </div>
          {field.helpText && <p className={styles.helpText}>{field.helpText}</p>}
          {onboardingNote}
          {fieldError && <p className={styles.errorText}>{fieldError}</p>}
        </div>
      );
    }

    if (field.type === 'date') {
      return (
        <div key={field.name} className={styles.field}>
          <label className={styles.label}>{field.label}</label>
          <div className={styles.dateRow}>
            <select className={styles.select} aria-label={`${field.label} month`}>
              <option value="">Month</option>
              {Array.from({ length: 12 }, (_, index) => (
                <option key={index + 1} value={index + 1}>{index + 1}</option>
              ))}
            </select>
            <select className={styles.select} aria-label={`${field.label} day`}>
              <option value="">Day</option>
              {Array.from({ length: 31 }, (_, index) => (
                <option key={index + 1} value={index + 1}>{index + 1}</option>
              ))}
            </select>
            <select className={styles.select} aria-label={`${field.label} year`}>
              <option value="">Year</option>
              {Array.from({ length: 10 }, (_, index) => {
                const year = new Date().getFullYear() + index;
                return <option key={year} value={year}>{year}</option>;
              })}
            </select>
          </div>
          {field.helpText && <p className={styles.helpText}>{field.helpText}</p>}
          {onboardingNote}
          {fieldError && <p className={styles.errorText}>{fieldError}</p>}
        </div>
      );
    }

    return (
      <div key={field.name} className={styles.field}>
        <label className={styles.label} htmlFor={field.name}>{field.label}</label>
        <input
          id={field.name}
          className={inputClassName}
          type={field.type === 'currency' || field.type === 'number' ? 'text' : field.type}
          inputMode={field.type === 'currency' || field.type === 'number' ? 'decimal' : undefined}
          value={formValues[field.name] ?? ''}
          onChange={(event) => {
            if (field.type === 'currency') {
              handleCurrencyChange(field, event.target.value);
              return;
            }
            handleFieldChange(field, event.target.value);
          }}
          placeholder={field.type === 'currency' ? '$0' : undefined}
        />
        {field.helpText && <p className={styles.helpText}>{field.helpText}</p>}
        {onboardingNote}
        {fieldError && <p className={styles.errorText}>{fieldError}</p>}
      </div>
    );
  };

  const pairedFieldNames = {
    home_purchase: ['homePrice', 'downPaymentPercent'],
    car_purchase: ['carPrice', 'downPaymentPercent'],
  };
  const pair = pairedFieldNames[goalType] ?? [];
  const pairedFields = definition?.fields.filter((field) => pair.includes(field.name)) ?? [];
  const remainingFields = definition?.fields.filter((field) => !pair.includes(field.name)) ?? [];

  return (
    <div className={styles.goalForm}>
      <h2 className={styles.heading}>What&apos;s your financial goal?</h2>
      <p className={styles.subheading}>Choose a goal and we&apos;ll map the smartest path to get there.</p>

      <div className={styles.goalTypeSelector}>
        <label className={styles.label} htmlFor="goalType">Select goal type</label>
        <select
          id="goalType"
          className={styles.select}
          value={goalType}
          onChange={handleGoalTypeChange}
        >
          <option value="">Choose...</option>
          {goalOptions.map((option) => (
            <option key={option.id} value={option.id}>{option.label}</option>
          ))}
        </select>
      </div>

      {definition && (
        <form onSubmit={handleSubmit}>
          <div className={styles.typeHeader}>
            <div className={styles.typeIcon}>
              <TypeIcon size={20} aria-hidden />
            </div>
            <div>
              <strong>{definition.label}</strong>
              <p className={styles.typeDescription}>{definition.description}</p>
            </div>
          </div>

          {formError && <div className={styles.formError} role="alert">{formError}</div>}

          <div className={styles.fieldGrid}>
            {pairedFields.length > 0 && (
              <div className={`${styles.fieldGroup} ${styles.fieldGroupPair}`}>
                {pairedFields.map(renderFormField)}
              </div>
            )}
            {remainingFields.map(renderFormField)}
          </div>

          <div className={styles.summary}>
            <h4>Your Goal</h4>
            <p>{summary || 'Fill in the fields above to see your goal summary.'}</p>
          </div>

          <div className={styles.actions}>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={!validation.isValid || isSubmitting}
            >
              {submitLabel ?? 'Analyze My Path'}
            </button>
            {isSubmitting && (
              <span className={styles.statusMessage}>
                <Loader2 size={16} className="inline animate-spin" aria-hidden />
                {' '}Analyzing...
              </span>
            )}
            {submitSuccess && !isSubmitting && (
              <span className={`${styles.statusMessage} ${styles.successMessage}`}>
                Goal submitted successfully.
              </span>
            )}
          </div>
        </form>
      )}
    </div>
  );
}

export {
  loadGoalDefinition,
  validateForm,
  formatCurrencyInput,
  generateGoalSummary,
  submitGoal,
};
