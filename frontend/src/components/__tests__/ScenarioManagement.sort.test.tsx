import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import {
  SCENARIO_STORAGE_KEY,
  updateScenario,
  type Scenario,
} from '../../utils/scenarioStorage';

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  })),
}));

const SORT_KEY = 'scenario_sort';

const SEED_SCENARIOS: Scenario[] = [
  {
    scenario_id: 'sc_alpha',
    calculator_type: 'retirement',
    name: 'Alpha Retirement',
    inputs: { currentAge: 35 },
    outputs: { projectedSavings: 100000 },
    notes: '',
    created_at: '2026-07-01T10:00:00.000Z',
    last_modified: '2026-07-01T10:00:00.000Z',
  },
  {
    scenario_id: 'sc_beta',
    calculator_type: 'mortgage',
    name: 'Beta Mortgage',
    inputs: { homePrice: 300000 },
    outputs: { monthlyPayment: 1800 },
    notes: '',
    created_at: '2026-07-02T10:00:00.000Z',
    last_modified: '2026-07-02T10:00:00.000Z',
  },
  {
    scenario_id: 'sc_gamma',
    calculator_type: 'tax',
    name: 'Gamma Tax',
    inputs: { grossIncome: 90000 },
    outputs: { estimatedTax: 15000 },
    notes: '',
    created_at: '2026-07-04T10:00:00.000Z',
    last_modified: '2026-07-04T10:00:00.000Z',
  },
];

function seedScenarios(): void {
  window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(SEED_SCENARIOS));
}

function getSortDropdown(): HTMLSelectElement {
  return screen.getAllByLabelText('Sort by')[0] as HTMLSelectElement;
}

function getRowNames(): string[] {
  const table = screen.getByRole('table');
  const rows = within(table).getAllByRole('row').slice(1);
  return rows.map((row) => within(row).getAllByRole('cell')[1].textContent ?? '');
}

function renderDashboard(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <ScenarioManagement />
    </MemoryRouter>,
  );
}

describe('ScenarioManagement sorting', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedScenarios();
  });

  it('shows all seeded scenarios on load', () => {
    renderDashboard();
    expect(getRowNames()).toHaveLength(3);
    expect(screen.getByText('Alpha Retirement')).toBeInTheDocument();
    expect(screen.getByText('Beta Mortgage')).toBeInTheDocument();
    expect(screen.getByText('Gamma Tax')).toBeInTheDocument();
  });

  it('defaults to most recently modified (newest first)', () => {
    renderDashboard();
    expect(getSortDropdown()).toHaveValue('recent');
    expect(getRowNames()).toEqual(['Gamma Tax', 'Beta Mortgage', 'Alpha Retirement']);
  });

  it('moves updated scenario to the top after refresh', () => {
    const first = renderDashboard();
    expect(getRowNames()[0]).toBe('Gamma Tax');

    updateScenario('sc_alpha', { notes: 'Updated just now' });
    first.unmount();

    renderDashboard();
    expect(getRowNames()[0]).toBe('Alpha Retirement');
  });

  it('sorts by oldest first', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getSortDropdown(), 'oldest');
    expect(getRowNames()).toEqual(['Alpha Retirement', 'Beta Mortgage', 'Gamma Tax']);
  });

  it('sorts alphabetically A-Z', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getSortDropdown(), 'alpha-asc');
    expect(getRowNames()).toEqual(['Alpha Retirement', 'Beta Mortgage', 'Gamma Tax']);
  });

  it('sorts alphabetically Z-A', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getSortDropdown(), 'alpha-desc');
    expect(getRowNames()).toEqual(['Gamma Tax', 'Beta Mortgage', 'Alpha Retirement']);
  });

  it('sorts by type then name within type', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getSortDropdown(), 'by-type');
    expect(getRowNames()).toEqual(['Alpha Retirement', 'Beta Mortgage', 'Gamma Tax']);
  });

  it('persists sort preference across remount (page refresh)', async () => {
    const user = userEvent.setup();
    const first = renderDashboard();

    await user.selectOptions(getSortDropdown(), 'alpha-asc');
    expect(window.localStorage.getItem(SORT_KEY)).toBe(JSON.stringify('alpha-asc'));
    expect(getRowNames()).toEqual(['Alpha Retirement', 'Beta Mortgage', 'Gamma Tax']);

    first.unmount();
    renderDashboard();

    expect(getSortDropdown()).toHaveValue('alpha-asc');
    expect(getRowNames()).toEqual(['Alpha Retirement', 'Beta Mortgage', 'Gamma Tax']);
  });
});
