import {
  SCENARIO_STORAGE_KEY,
  deleteScenario,
  duplicateScenario,
  getScenario,
  loadScenarios,
  saveScenario,
  updateScenario,
} from '../scenarioStorage';

describe('scenarioStorage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('saves and lists scenarios in the expected schema', () => {
    const saved = saveScenario({
      calculator_type: 'retirement',
      name: 'Retire at 58',
      inputs: {
        current_age: 45,
        current_savings: 220000,
      },
      outputs: {
        retirement_age: 58,
        gap: 0,
      },
      notes: 'Conservative estimate',
    });

    expect(saved.scenario_id).toMatch(/^sc_/);
    expect(saved.calculator_type).toBe('retirement');
    expect(saved.name).toBe('Retire at 58');
    expect(saved.inputs.current_age).toBe(45);
    expect(saved.outputs.retirement_age).toBe(58);
    expect(saved.notes).toBe('Conservative estimate');
    expect(saved.created_at).toEqual(saved.last_modified);

    const rawStorage = window.localStorage.getItem(SCENARIO_STORAGE_KEY);
    expect(rawStorage).not.toBeNull();

    const listed = loadScenarios();
    expect(listed).toHaveLength(1);
    expect(listed[0]).toMatchObject({
      scenario_id: saved.scenario_id,
      calculator_type: 'retirement',
      name: 'Retire at 58',
    });
  });

  it('renames, duplicates, and deletes scenarios', () => {
    const original = saveScenario({
      calculator_type: 'mortgage',
      name: 'Starter home',
      inputs: {
        home_price: 350000,
      },
      outputs: {
        monthly_payment: 2400,
      },
      notes: '',
    });

    const renamed = updateScenario(original.scenario_id, {
      name: 'Starter home - Updated',
    });
    expect(renamed?.name).toBe('Starter home - Updated');
    expect(getScenario(original.scenario_id)?.name).toBe('Starter home - Updated');

    const duplicate = duplicateScenario(original.scenario_id, 'Starter home - Copy');
    expect(duplicate).not.toBeNull();
    expect(duplicate?.scenario_id).not.toBe(original.scenario_id);
    expect(duplicate?.name).toBe('Starter home - Copy');
    expect(duplicate?.inputs.home_price).toBe(350000);

    expect(loadScenarios()).toHaveLength(2);

    const deleted = deleteScenario(original.scenario_id);
    expect(deleted).toBe(true);
    expect(getScenario(original.scenario_id)).toBeNull();
    expect(loadScenarios()).toHaveLength(1);
  });
});
