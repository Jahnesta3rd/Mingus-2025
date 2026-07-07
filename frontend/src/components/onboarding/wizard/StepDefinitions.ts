import React from 'react';
import type { ModuleId } from '../../../types/modularOnboarding';
import { PlaceholderStep } from './steps/PlaceholderStep';
import AcquisitionSourceStep from './steps/AcquisitionSourceStep';
import IncomeStep from './steps/IncomeStep';
import RecurringExpensesStep from './steps/RecurringExpensesStep';
import HousingStep from './steps/HousingStep';
import VehicleStep from './steps/VehicleStep';
import RosterStep from './steps/RosterStep';
import CareerStep from './steps/CareerStep';
import MilestonesStep from './steps/MilestonesStep';
import GoalIntentStep from './steps/GoalIntentStep';

export interface StepProps {
  stepLabel: string;
  initialData: Record<string, unknown>;
  onSubmit: (data: Record<string, unknown>) => void | Promise<void>;
  onSkip: () => void;
  isSubmitting: boolean;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export type WizardStepId = ModuleId | 'goal_intent';

export type StepDefinition = {
  id: WizardStepId;
  label: string;
  Component: React.ComponentType<StepProps>;
  allowSkip: boolean;
  commitOnSubmit?: boolean;
  /** Client-only steps are not persisted to modular-onboarding API */
  clientOnly?: boolean;
};

export const BACKEND_MODULE_IDS: ModuleId[] = [
  'acquisition_source',
  'income',
  'housing',
  'vehicle',
  'recurring_expenses',
  'roster',
  'career',
  'milestones',
];

export const STEP_ORDER: StepDefinition[] = [
  { id: 'acquisition_source', label: 'How did you find us?', Component: AcquisitionSourceStep, allowSkip: true, commitOnSubmit: true },
  { id: 'goal_intent', label: 'Financial goal', Component: GoalIntentStep, allowSkip: true, commitOnSubmit: false, clientOnly: true },
  { id: 'income',             label: 'Income',             Component: IncomeStep,             allowSkip: true, commitOnSubmit: true },
  { id: 'housing',            label: 'Housing',            Component: HousingStep,            allowSkip: true, commitOnSubmit: true },
  { id: 'vehicle',            label: 'Vehicle',            Component: VehicleStep,            allowSkip: true, commitOnSubmit: true },
  { id: 'recurring_expenses', label: 'Recurring Expenses', Component: RecurringExpensesStep, allowSkip: true, commitOnSubmit: true },
  { id: 'roster',             label: 'Roster',             Component: RosterStep,             allowSkip: true, commitOnSubmit: true },
  { id: 'career',             label: 'Career',             Component: CareerStep,             allowSkip: true, commitOnSubmit: true },
  { id: 'milestones',         label: 'Important dates',  Component: MilestonesStep,         allowSkip: true, commitOnSubmit: true },
];
