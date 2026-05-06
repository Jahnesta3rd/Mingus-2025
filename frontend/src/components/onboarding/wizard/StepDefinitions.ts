import React from 'react';
import type { ModuleId } from '../../../types/modularOnboarding';
import { PlaceholderStep } from './steps/PlaceholderStep';
import IncomeStep from './steps/IncomeStep';
import RecurringExpensesStep from './steps/RecurringExpensesStep';

export interface StepProps {
  stepLabel: string;
  initialData: Record<string, unknown>;
  onSubmit: (data: Record<string, unknown>) => void | Promise<void>;
  onSkip: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export type StepDefinition = {
  id: ModuleId;
  label: string;
  Component: React.ComponentType<StepProps>;
  allowSkip: boolean;
  commitOnSubmit?: boolean;
};

export const STEP_ORDER: StepDefinition[] = [
  { id: 'income',             label: 'Income',             Component: IncomeStep,             allowSkip: true, commitOnSubmit: true },
  { id: 'housing',            label: 'Housing',            Component: PlaceholderStep,        allowSkip: true },
  { id: 'vehicle',            label: 'Vehicle',            Component: PlaceholderStep,        allowSkip: true },
  { id: 'recurring_expenses', label: 'Recurring Expenses', Component: RecurringExpensesStep, allowSkip: true, commitOnSubmit: true },
  { id: 'roster',             label: 'Roster',             Component: PlaceholderStep,        allowSkip: true },
  { id: 'career',             label: 'Career',             Component: PlaceholderStep,        allowSkip: true },
  { id: 'milestones',         label: 'Milestones',         Component: PlaceholderStep,        allowSkip: true },
];
