import { BABY_CATEGORIES } from '../data/milestoneCategories';

export type OnboardingModuleData = {
  goal_intent?: {
    goal_intent?: string;
    interested?: boolean;
  };
  housing?: {
    has_buy_goal?: boolean;
    target_price?: number;
    target_timeline_months?: number;
    down_payment_saved?: number;
    monthly_cost?: number;
  };
  income?: {
    monthly_takehome?: number;
    has_secondary?: boolean;
    secondary_amount?: number;
  };
  milestones?: {
    events?: Array<{
      name?: string;
      date?: string;
      event_date?: string;
      cost?: number;
      estimated_cost?: number;
      type?: string;
      category?: string;
    }>;
  };
  recurring_expenses?: {
    categories?: Record<string, number>;
  };
  financial_info?: {
    income?: number;
    savings?: number;
  };
  important_dates?: {
    births?: unknown[];
  };
  goals?: {
    list?: unknown[];
    timeline?: number;
  };
};

export type GoalFormPrefillResult = {
  homePrice?: number;
  hasHousingGoal?: boolean;
  statedGoals?: unknown[];
  timeline?: number;
  recentBabyEvent?: boolean;
  annualIncome?: number;
  currentSavings?: number;
  goalIntent: string | null;
  hasGoalInterest: boolean;
  suggestedGoalType: string | null;
  defaultValues: {
    type: string;
    parameters: Record<string, number>;
    timeline?: number;
  } | null;
  prefilledFields: string[];
};

const INTENT_TO_GOAL_TYPE: Record<string, string> = {
  home_purchase: 'home_purchase',
  car_purchase: 'car_purchase',
  apartment_move: 'apartment_move',
  business: 'business',
  baby: 'baby',
  side_income: 'business',
  debt_payoff: 'home_purchase',
};

function toNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value.replace(/,/g, ''));
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
}

function monthsToYears(months: number): number {
  return Math.max(0.25, Math.round((months / 12) * 10) / 10);
}

/**
 * Extracts goal-relevant onboarding data and builds GoalForm defaults.
 */
export function buildGoalFormPrefill(onboardingData?: OnboardingModuleData | null): GoalFormPrefillResult {
  const housing = onboardingData?.housing;
  const income = onboardingData?.income;
  const events = onboardingData?.milestones?.events ?? [];
  const goalIntentRaw = onboardingData?.goal_intent?.goal_intent ?? null;
  const interested = onboardingData?.goal_intent?.interested;

  const hasGoalInterest = interested === true
    || (typeof goalIntentRaw === 'string'
      && goalIntentRaw !== ''
      && goalIntentRaw !== 'prefer_not_to_say');

  let suggestedGoalType = goalIntentRaw ? INTENT_TO_GOAL_TYPE[goalIntentRaw] ?? null : null;
  const parameters: Record<string, number> = {};
  const prefilledFields: string[] = [];
  let timeline: number | undefined;

  if (housing?.has_buy_goal) {
    suggestedGoalType = suggestedGoalType ?? 'home_purchase';
    const price = toNumber(housing.target_price);
    if (price) {
      parameters.homePrice = price;
      prefilledFields.push('homePrice');
    }
    const saved = toNumber(housing.down_payment_saved);
    if (saved !== undefined && saved >= 0) {
      parameters.savedAmount = saved;
      prefilledFields.push('savedAmount');
    }
    const months = toNumber(housing.target_timeline_months);
    if (months) {
      timeline = monthsToYears(months);
      prefilledFields.push('timeline');
    }
  }

  const rent = toNumber(housing?.monthly_cost);
  if (suggestedGoalType === 'apartment_move' && rent) {
    parameters.monthlyRent = rent;
    prefilledFields.push('monthlyRent');
  }

  for (const event of events) {
    const category = event.category ?? event.type ?? '';
    const cost = toNumber(event.cost ?? event.estimated_cost);

    if (category === 'home_purchase' && cost) {
      suggestedGoalType = suggestedGoalType ?? 'home_purchase';
      parameters.homePrice = cost;
      if (!prefilledFields.includes('homePrice')) {
        prefilledFields.push('homePrice');
      }
    }

    if (category === 'car_purchase' && cost) {
      suggestedGoalType = suggestedGoalType ?? 'car_purchase';
      parameters.carPrice = cost;
      prefilledFields.push('carPrice');
    }

    if (BABY_CATEGORIES.includes(category as typeof BABY_CATEGORIES[number])) {
      suggestedGoalType = suggestedGoalType ?? 'baby';
      if (cost) {
        parameters.preparationCost = cost;
        prefilledFields.push('preparationCost');
      }
    }

    if (category === 'moving' && cost) {
      suggestedGoalType = suggestedGoalType ?? 'apartment_move';
      parameters.movingCosts = cost;
      prefilledFields.push('movingCosts');
    }
  }

  const monthlyTakehome = toNumber(income?.monthly_takehome);
  const annualIncome = monthlyTakehome ? monthlyTakehome * 12 : toNumber(onboardingData?.financial_info?.income);
  const currentSavings = toNumber(housing?.down_payment_saved)
    ?? toNumber(onboardingData?.financial_info?.savings);

  if (currentSavings !== undefined && !prefilledFields.includes('savedAmount')) {
    parameters.savedAmount = currentSavings;
    prefilledFields.push('savedAmount');
  }

  const recentBabyEvent = events.some((event) => {
    const category = event.category ?? event.type ?? '';
    return BABY_CATEGORIES.includes(category as typeof BABY_CATEGORIES[number]);
  }) || (onboardingData?.important_dates?.births?.length ?? 0) > 0;

  const defaultValues = suggestedGoalType
    ? {
      type: suggestedGoalType,
      parameters,
      ...(timeline !== undefined ? { timeline } : {}),
    }
    : null;

  return {
    homePrice: parameters.homePrice,
    hasHousingGoal: housing?.has_buy_goal === true,
    statedGoals: onboardingData?.goals?.list,
    timeline: timeline ?? onboardingData?.goals?.timeline,
    recentBabyEvent,
    annualIncome,
    currentSavings,
    goalIntent: goalIntentRaw,
    hasGoalInterest,
    suggestedGoalType,
    defaultValues,
    prefilledFields: [...new Set(prefilledFields)],
  };
}

export function useGoalFormPrefill(onboardingData?: OnboardingModuleData | null): GoalFormPrefillResult {
  return buildGoalFormPrefill(onboardingData);
}

export const ONBOARDING_PREFILL_STORAGE_KEY = 'mingus_onboarding_goal_prefill';
export const ONBOARDING_GOAL_ROUTE_KEY = 'mingus_onboarding_goal_route';

export function persistOnboardingPrefill(onboardingData: OnboardingModuleData): GoalFormPrefillResult {
  const prefill = buildGoalFormPrefill(onboardingData);
  try {
    sessionStorage.setItem(ONBOARDING_PREFILL_STORAGE_KEY, JSON.stringify({
      onboardingData,
      prefill,
    }));
    if (prefill.hasGoalInterest && prefill.suggestedGoalType) {
      sessionStorage.setItem(ONBOARDING_GOAL_ROUTE_KEY, 'goal-planning');
    } else {
      sessionStorage.removeItem(ONBOARDING_GOAL_ROUTE_KEY);
    }
  } catch {
    /* ignore storage errors */
  }
  return prefill;
}

export function readStoredOnboardingPrefill(): {
  onboardingData: OnboardingModuleData;
  prefill: GoalFormPrefillResult;
} | null {
  try {
    const raw = sessionStorage.getItem(ONBOARDING_PREFILL_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as {
      onboardingData: OnboardingModuleData;
      prefill: GoalFormPrefillResult;
    };
  } catch {
    return null;
  }
}

export function clearStoredOnboardingPrefill(): void {
  try {
    sessionStorage.removeItem(ONBOARDING_PREFILL_STORAGE_KEY);
    sessionStorage.removeItem(ONBOARDING_GOAL_ROUTE_KEY);
  } catch {
    /* ignore */
  }
}
