import React from 'react';
import { PlaceholderStep } from './steps/PlaceholderStep';

export interface StepProps {
  stepLabel: string;
  initialData: Record<string, unknown>;
  onSubmit: (data: Record<string, unknown>) => void | Promise<void>;
  onSkip: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export interface StepDefinition {
  id: string;
  label: string;
  Component: React.ComponentType<StepProps>;
  allowSkip: boolean;
}

export const STEP_ORDER: StepDefinition[] = [
  { id: 'income',             label: 'Income',             Component: PlaceholderStep, allowSkip: true },
  { id: 'housing',            label: 'Housing',            Component: PlaceholderStep, allowSkip: true },
  { id: 'vehicle',            label: 'Vehicle',            Component: PlaceholderStep, allowSkip: true },
  { id: 'recurring_expenses', label: 'Recurring Expenses', Component: PlaceholderStep, allowSkip: true },
  { id: 'roster',             label: 'Roster',             Component: PlaceholderStep, allowSkip: true },
  { id: 'career',             label: 'Career',             Component: PlaceholderStep, allowSkip: true },
  { id: 'milestones',         label: 'Milestones',         Component: PlaceholderStep, allowSkip: true },
];
