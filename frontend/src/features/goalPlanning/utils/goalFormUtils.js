import { loadGoalDefinition } from '../goalDefinitions/index.ts';

/**
 * @param {unknown} value
 * @returns {number | null}
 */
function toNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value.replace(/,/g, ''));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

/**
 * Parses a currency string into a number.
 * @param {string} raw
 * @returns {number | null}
 */
export function parseCurrencyInput(raw) {
  if (raw === '' || raw == null) {
    return null;
  }
  const cleaned = String(raw).replace(/[^0-9.]/g, '');
  if (!cleaned) {
    return null;
  }
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Formats a number as USD currency text for inputs.
 * @param {number | string | null | undefined} value
 * @returns {string}
 */
export function formatCurrencyInput(value) {
  const numeric = toNumber(value);
  if (numeric == null) {
    return '';
  }
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0,
  }).format(numeric);
}

/**
 * Formats a number as display currency.
 * @param {number | null | undefined} value
 * @returns {string}
 */
export function formatCurrencyDisplay(value) {
  const numeric = toNumber(value);
  if (numeric == null) {
    return '$0';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(numeric);
}

/**
 * Builds initial form values from defaults and optional goal.
 * @param {object | null} definition
 * @param {object} [defaultValues]
 * @returns {Record<string, string | number>}
 */
export function buildInitialFormValues(definition, defaultValues) {
  if (!definition) {
    return {};
  }

  const values = {};
  const parameters = defaultValues?.parameters ?? {};

  definition.fields.forEach((field) => {
    const existing = parameters[field.name] ?? defaultValues?.[field.name];
    if (existing !== undefined && existing !== null && existing !== '') {
      values[field.name] = field.type === 'currency'
        ? formatCurrencyInput(existing)
        : existing;
      return;
    }
    if (field.default !== undefined) {
      values[field.name] = field.type === 'currency'
        ? formatCurrencyInput(field.default)
        : field.default;
    } else {
      values[field.name] = field.type === 'percent' ? 0 : '';
    }
  });

  return values;
}

/**
 * Validates form values against a goal definition.
 * @param {object | null} definition
 * @param {Record<string, unknown>} formValues
 * @returns {{ isValid: boolean, errors: Record<string, string> }}
 */
export function validateForm(definition, formValues) {
  const errors = {};

  if (!definition) {
    return { isValid: false, errors: { goalType: 'Select a goal type.' } };
  }

  definition.fields.forEach((field) => {
    const raw = formValues[field.name];
    const isEmpty = raw === '' || raw === null || raw === undefined;

    if (field.required && isEmpty) {
      errors[field.name] = `${field.label} is required.`;
      return;
    }

    if (isEmpty) {
      return;
    }

    let numeric = null;
    if (field.type === 'currency') {
      numeric = parseCurrencyInput(String(raw));
      if (numeric == null) {
        errors[field.name] = `${field.label} must be a valid amount.`;
        return;
      }
      const minValue = field.min ?? (field.required ? 1 : 0);
      if (numeric < minValue) {
        errors[field.name] = `${field.label} must be at least ${formatCurrencyDisplay(minValue)}.`;
        return;
      }
    }

    if (field.type === 'number' || field.type === 'percent') {
      numeric = toNumber(raw);
      if (numeric == null) {
        errors[field.name] = `${field.label} must be a valid number.`;
        return;
      }
      if (numeric <= 0 && field.name === 'timeline') {
        errors[field.name] = `${field.label} must be greater than zero.`;
      }
      if (field.min != null && numeric < field.min) {
        errors[field.name] = `${field.label} must be at least ${field.min}.`;
      }
      if (field.max != null && numeric > field.max) {
        errors[field.name] = `${field.label} must be no more than ${field.max}.`;
      }
    }
  });

  return { isValid: Object.keys(errors).length === 0, errors };
}

/**
 * Parses a field value for submission.
 * @param {object} field
 * @param {unknown} raw
 * @returns {number | undefined}
 */
function parseFieldValue(field, raw) {
  if (raw === '' || raw == null) {
    return undefined;
  }
  if (field.type === 'currency') {
    return parseCurrencyInput(String(raw)) ?? undefined;
  }
  return toNumber(raw) ?? undefined;
}

/**
 * Builds analyzer-compatible goal payload from form values.
 * @param {string} goalType
 * @param {Record<string, unknown>} formValues
 * @returns {object | null}
 */
export function submitGoal(goalType, formValues) {
  const definition = loadGoalDefinition(goalType);
  if (!definition) {
    return null;
  }

  const { isValid } = validateForm(definition, formValues);
  if (!isValid) {
    return null;
  }

  const parameters = {};
  definition.fields.forEach((field) => {
    if (field.name === 'timeline') {
      return;
    }
    const parsed = parseFieldValue(field, formValues[field.name]);
    if (parsed !== undefined) {
      parameters[field.name] = parsed;
    }
  });

  if (parameters.savedAmount !== undefined) {
    parameters.downPaymentAmount = parameters.savedAmount;
  }

  const timelineRaw = parseFieldValue(
    definition.fields.find((field) => field.name === 'timeline') ?? { type: 'number' },
    formValues.timeline,
  );

  let timeline = timelineRaw ?? 1;
  if (definition.timelineUnit === 'months') {
    timeline = Math.max(1 / 12, timeline / 12);
  }

  return {
    type: goalType,
    parameters,
    timeline,
    constraints: [],
  };
}

/**
 * Generates a readable goal summary.
 * @param {string} goalType
 * @param {Record<string, unknown>} formValues
 * @returns {string}
 */
export function generateGoalSummary(goalType, formValues) {
  const definition = loadGoalDefinition(goalType);
  if (!definition) {
    return '';
  }

  switch (goalType) {
    case 'home_purchase': {
      const price = parseCurrencyInput(String(formValues.homePrice ?? ''));
      const percent = toNumber(formValues.downPaymentPercent) ?? 0;
      const timeline = toNumber(formValues.timeline) ?? 0;
      const saved = parseCurrencyInput(String(formValues.savedAmount ?? '')) ?? 0;
      const downPayment = price ? Math.round(price * (percent / 100)) : 0;
      return `Buy a home for ${formatCurrencyDisplay(price)} with a ${percent}% down payment (${formatCurrencyDisplay(downPayment)}) in ${timeline} years. ${saved > 0 ? `You already have ${formatCurrencyDisplay(saved)} saved.` : ''}`.trim();
    }
    case 'car_purchase': {
      const price = parseCurrencyInput(String(formValues.carPrice ?? ''));
      const percent = toNumber(formValues.downPaymentPercent) ?? 0;
      const timeline = toNumber(formValues.timeline) ?? 0;
      return `Buy a car for ${formatCurrencyDisplay(price)} with ${percent}% down in ${timeline} years.`;
    }
    case 'apartment_move': {
      const rent = parseCurrencyInput(String(formValues.monthlyRent ?? ''));
      const moving = parseCurrencyInput(String(formValues.movingCosts ?? '')) ?? 0;
      const months = toNumber(formValues.timeline) ?? 0;
      return `Move to an apartment at ${formatCurrencyDisplay(rent)}/month in ${months} months with ${formatCurrencyDisplay(moving)} in moving costs.`;
    }
    case 'baby': {
      const budget = parseCurrencyInput(String(formValues.preparationCost ?? ''));
      const timeline = toNumber(formValues.timeline) ?? 0;
      return `Prepare ${formatCurrencyDisplay(budget)} for a new baby over ${timeline} years.`;
    }
    case 'business': {
      const investment = parseCurrencyInput(String(formValues.initialInvestment ?? ''));
      const monthly = parseCurrencyInput(String(formValues.monthlyCost ?? ''));
      const timeline = toNumber(formValues.timeline) ?? 0;
      return `Launch a business with ${formatCurrencyDisplay(investment)} upfront and ${formatCurrencyDisplay(monthly)}/month operating costs in ${timeline} years.`;
    }
    default:
      return definition.description ?? 'Financial goal';
  }
}

export { loadGoalDefinition };
