export const SCENARIO_STORAGE_KEY = 'mingus_financial_scenarios';

export interface Scenario {
  scenario_id: string;
  calculator_type: string;
  name: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  notes: string;
  created_at: string;
  last_modified: string;
}

interface SaveScenarioInput {
  scenario_id?: string;
  calculator_type: string;
  name: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  notes?: string;
  created_at?: string;
}

function canUseLocalStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function cloneRecord<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function createScenarioId(): string {
  return `sc_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function readScenarioList(): Scenario[] {
  if (!canUseLocalStorage()) return [];

  const raw = window.localStorage.getItem(SCENARIO_STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as Scenario[]) : [];
  } catch {
    return [];
  }
}

function writeScenarioList(scenarios: Scenario[]): void {
  if (!canUseLocalStorage()) return;
  window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenarios));
}

export function loadScenarios(): Scenario[] {
  return readScenarioList().sort((left, right) =>
    right.last_modified.localeCompare(left.last_modified),
  );
}

export function getScenariosByType(calculatorType: string): Scenario[] {
  return loadScenarios().filter((scenario) => scenario.calculator_type === calculatorType);
}

export function listScenarios(): Scenario[] {
  return loadScenarios();
}

export function getScenario(scenarioId: string): Scenario | null {
  return loadScenarios().find((scenario) => scenario.scenario_id === scenarioId) ?? null;
}

export function saveScenario(input: SaveScenarioInput): Scenario {
  const existing = input.scenario_id ? getScenario(input.scenario_id) : null;
  const scenarios = readScenarioList().filter(
    (scenario) => scenario.scenario_id !== existing?.scenario_id,
  );
  const now = new Date().toISOString();

  const scenario: Scenario = {
    scenario_id: existing?.scenario_id ?? input.scenario_id ?? createScenarioId(),
    calculator_type: input.calculator_type,
    name: input.name.trim(),
    inputs: cloneRecord(input.inputs),
    outputs: cloneRecord(input.outputs),
    notes: input.notes?.trim() ?? '',
    created_at: existing?.created_at ?? input.created_at ?? now,
    last_modified: now,
  };

  scenarios.push(scenario);
  writeScenarioList(scenarios);

  return scenario;
}

export function updateScenario(
  scenarioId: string,
  updates: Partial<Omit<Scenario, 'scenario_id' | 'created_at' | 'last_modified'>>,
): Scenario | null {
  const scenario = getScenario(scenarioId);
  if (!scenario) return null;

  return saveScenario({
    scenario_id: scenario.scenario_id,
    created_at: scenario.created_at,
    calculator_type: updates.calculator_type ?? scenario.calculator_type,
    name: updates.name ?? scenario.name,
    inputs: updates.inputs ?? scenario.inputs,
    outputs: updates.outputs ?? scenario.outputs,
    notes: updates.notes ?? scenario.notes,
  });
}

export function duplicateScenario(
  scenarioId: string,
  duplicateName?: string,
): Scenario | null {
  const scenario = getScenario(scenarioId);
  if (!scenario) return null;

  return saveScenario({
    calculator_type: scenario.calculator_type,
    name: duplicateName ?? `${scenario.name} - Copy`,
    inputs: scenario.inputs,
    outputs: scenario.outputs,
    notes: scenario.notes,
  });
}

export function deleteScenario(scenarioId: string): boolean {
  const scenarios = readScenarioList();
  const remaining = scenarios.filter((scenario) => scenario.scenario_id !== scenarioId);

  if (remaining.length === scenarios.length) {
    return false;
  }

  writeScenarioList(remaining);
  return true;
}

export type SavedScenario = Scenario;

export function renameScenario(scenarioId: string, nextName: string): Scenario | null {
  return updateScenario(scenarioId, { name: nextName });
}
