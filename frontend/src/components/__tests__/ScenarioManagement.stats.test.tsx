import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import {
  SCENARIO_STORAGE_KEY,
  saveScenario,
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

function renderDashboard(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <ScenarioManagement />
    </MemoryRouter>,
  );
}

function getStatValue(label: string): number {
  const labelEl = screen.getByText(label);
  const valueEl = labelEl.nextElementSibling;
  return Number(valueEl?.textContent ?? 0);
}

function getStatCard(label: string): HTMLElement {
  const labelEl = screen.getByText(label);
  return labelEl.closest('.rounded-2xl') as HTMLElement;
}

describe('ScenarioManagement statistics', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('shows four stat cards with icons and colored backgrounds when empty', () => {
    renderDashboard();

    expect(screen.getByText('Total Scenarios')).toBeInTheDocument();
    expect(screen.getByText('Retirement Plans')).toBeInTheDocument();
    expect(screen.getByText('Mortgage Plans')).toBeInTheDocument();
    expect(screen.getByText('Tax Plans')).toBeInTheDocument();

    expect(getStatValue('Total Scenarios')).toBe(0);
    expect(getStatValue('Retirement Plans')).toBe(0);
    expect(getStatValue('Mortgage Plans')).toBe(0);
    expect(getStatValue('Tax Plans')).toBe(0);

    expect(getStatCard('Total Scenarios')).toHaveClass('bg-white');
    expect(getStatCard('Total Scenarios').querySelector('svg')).toBeTruthy();
    expect(getStatCard('Retirement Plans')).toHaveClass('bg-blue-50');
    expect(getStatCard('Mortgage Plans')).toHaveClass('bg-green-50');
    expect(getStatCard('Tax Plans')).toHaveClass('bg-orange-50');
  });

  it('displays accurate counts for seeded scenarios', () => {
    seedScenarios();
    renderDashboard();

    expect(getStatValue('Total Scenarios')).toBe(3);
    expect(getStatValue('Retirement Plans')).toBe(1);
    expect(getStatValue('Mortgage Plans')).toBe(1);
    expect(getStatValue('Tax Plans')).toBe(1);
  });

  it('increments total and retirement counts when a retirement scenario is added', () => {
    seedScenarios();
    const first = renderDashboard();

    expect(getStatValue('Total Scenarios')).toBe(3);
    expect(getStatValue('Retirement Plans')).toBe(1);

    saveScenario({
      calculator_type: 'retirement',
      name: 'New Retirement Plan',
      inputs: { currentAge: 40 },
      outputs: { projectedSavings: 200000 },
      notes: '',
    });

    first.unmount();
    renderDashboard();

    expect(getStatValue('Total Scenarios')).toBe(4);
    expect(getStatValue('Retirement Plans')).toBe(2);
    expect(getStatValue('Mortgage Plans')).toBe(1);
    expect(getStatValue('Tax Plans')).toBe(1);
  });

  it('decrements total and mortgage counts when a mortgage scenario is deleted', async () => {
    const user = userEvent.setup();
    seedScenarios();
    renderDashboard();

    expect(getStatValue('Total Scenarios')).toBe(3);
    expect(getStatValue('Mortgage Plans')).toBe(1);

    const table = screen.getByRole('table');
    const mortgageRow = within(table)
      .getAllByRole('row')
      .find((row) => within(row).queryByText('Beta Mortgage'));
    expect(mortgageRow).toBeDefined();

    await user.click(within(mortgageRow!).getByRole('button', { name: 'Delete' }));
    const confirmDelete = screen
      .getAllByRole('button', { name: 'Delete' })
      .find((button) => button.className.includes('bg-red-600'));
    await user.click(confirmDelete!);

    expect(getStatValue('Total Scenarios')).toBe(2);
    expect(getStatValue('Mortgage Plans')).toBe(0);
    expect(getStatValue('Retirement Plans')).toBe(1);
    expect(getStatValue('Tax Plans')).toBe(1);
  });
});
