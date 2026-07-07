import home from './home.json';
import car from './car.json';
import apartment from './apartment.json';
import baby from './baby.json';
import business from './business.json';

export type GoalFieldType = 'currency' | 'number' | 'percent' | 'date' | 'text';

export interface GoalFieldDefinition {
  name: string;
  label: string;
  type: GoalFieldType;
  required?: boolean;
  default?: number;
  min?: number;
  max?: number;
  helpText?: string;
}

export interface GoalDefinition {
  id: string;
  label: string;
  icon: string;
  description: string;
  timelineUnit?: 'years' | 'months';
  fields: GoalFieldDefinition[];
}

/** @type {Record<string, GoalDefinition>} */
export const GOAL_DEFINITIONS: Record<string, GoalDefinition> = {
  home_purchase: home as GoalDefinition,
  car_purchase: car as GoalDefinition,
  apartment_move: apartment as GoalDefinition,
  baby: baby as GoalDefinition,
  business: business as GoalDefinition,
};

export const ALL_GOAL_DEFINITIONS: GoalDefinition[] = [
  home as GoalDefinition,
  car as GoalDefinition,
  apartment as GoalDefinition,
  baby as GoalDefinition,
  business as GoalDefinition,
];

/**
 * Loads a goal type configuration by id.
 */
export function loadGoalDefinition(goalType: string): GoalDefinition | null {
  if (!goalType || typeof goalType !== 'string') {
    return null;
  }
  return GOAL_DEFINITIONS[goalType] ?? null;
}

/**
 * Returns definitions filtered to supported goal type ids.
 */
export function getGoalTypeOptions(goalTypes?: string[]): GoalDefinition[] {
  if (!Array.isArray(goalTypes) || goalTypes.length === 0) {
    return ALL_GOAL_DEFINITIONS;
  }
  return goalTypes
    .map((goalType) => GOAL_DEFINITIONS[goalType])
    .filter(Boolean);
}

export default GOAL_DEFINITIONS;
