import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import { SCENARIO_STORAGE_KEY, type Scenario } from '../../utils/scenarioStorage';

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
    inputs: {
      currentAge: 35,
      retirementAge: 65,
      currentSavings: 85000,
    },
    outputs: {
      projectedSavings: 500000,
      yearsToRetirement: 30,
    },
    notes: 'Conservative growth assumptions',
    created_at: '2026-07-01T14:30:00.000Z',
    last_modified: '2026-07-04T14:30:00.000Z',
  },
  {
    scenario_id: 'sc_beta',
    calculator_type: 'mortgage',
    name: 'Beta Mortgage',
    inputs: { homePrice: 300000, downPayment: 60000 },
    outputs: { monthlyPayment: 1800 },
    notes: '',
    created_at: '2026-07-02T10:00:00.000Z',
    last_modified: '2026-07-02T10:00:00.000Z',
  },
  {
    scenario_id: 'sc_gamma',
    calculator_type: 'tax',
    name: 'Gamma Tax',
    inputs: { grossIncome: 90000, deductions: 12000 },
    outputs: { estimatedTax: 15000, effectiveRate: 19.2 },
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

function getDetailPanel(): HTMLElement | null {
  return document.querySelector('aside.fixed.right-0');
}

function getListRowByName(name: string): HTMLElement {
  const table = screen.getByRole('table');
  const row = within(table)
    .getAllByRole('row')
    .find((candidate) => within(candidate).queryByText(name));
  if (!row) throw new Error(`Row not found for ${name}`);
  return row;
}

function getScenarioCards(): HTMLElement[] {
  return screen
    .queryAllByRole('heading', { level: 3 })
    .map((heading) => heading.closest('article'))
    .filter((card): card is HTMLElement => card !== null);
}

function openViewForScenario(name: string): Promise<void> {
  const user = userEvent.setup();
  const row = getListRowByName(name);
  return user.click(within(row).getByRole('button', { name: 'View' }));
}

describe('ScenarioManagement detail panel', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedScenarios();
  });

  it('opens from View and shows formatted scenario details', async () => {
    renderDashboard();
    await openViewForScenario('Alpha Retirement');

    const panel = getDetailPanel();
    expect(panel).toBeTruthy();
    expect(panel).toHaveClass('fixed', 'right-0', 'shadow-lg');

    expect(within(panel!).getByRole('heading', { name: 'Alpha Retirement', level: 2 })).toBeInTheDocument();
    expect(within(panel!).getByText('Retirement')).toHaveClass('bg-blue-100', 'text-blue-800');

    expect(within(panel!).getByText('Inputs')).toBeInTheDocument();
    expect(within(panel!).getByText('Current Age')).toBeInTheDocument();
    expect(within(panel!).getByText('35')).toBeInTheDocument();
    expect(within(panel!).getByText('Retirement Age')).toBeInTheDocument();
    expect(within(panel!).getByText('Current Savings')).toBeInTheDocument();
    expect(within(panel!).getByText('$85,000')).toBeInTheDocument();

    expect(within(panel!).getByText('Outputs')).toBeInTheDocument();
    expect(within(panel!).getByText('Projected Savings')).toBeInTheDocument();
    expect(within(panel!).getByText('$500,000')).toBeInTheDocument();
    expect(within(panel!).getByText('Years to Retirement')).toBeInTheDocument();
    expect(within(panel!).getByText('30')).toBeInTheDocument();

    expect(within(panel!).getByText('Notes')).toBeInTheDocument();
    expect(within(panel!).getByText('Conservative growth assumptions')).toBeInTheDocument();

    expect(panel!.textContent).toMatch(/Created:.*Jul 1, 2026/);
    expect(panel!.textContent).toMatch(/Last modified:.*Jul 4, 2026/);
    expect(panel!.textContent).toMatch(/\d{1,2}:\d{2}/);

    expect(screen.getByRole('heading', { name: 'Scenario Management', level: 1 })).toBeInTheDocument();
  });

  it('closes when clicking the X button', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await openViewForScenario('Gamma Tax');

    expect(getDetailPanel()).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Close detail panel' }));
    expect(getDetailPanel()).toBeNull();
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('closes when clicking the overlay', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await openViewForScenario('Gamma Tax');

    expect(getDetailPanel()).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Close detail panel overlay' }));
    expect(getDetailPanel()).toBeNull();
  });

  it('switches to a different scenario without duplicate panels', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await openViewForScenario('Alpha Retirement');
    expect(within(getDetailPanel()!).getByRole('heading', { name: 'Alpha Retirement', level: 2 })).toBeInTheDocument();

    await user.click(within(getListRowByName('Beta Mortgage')).getByRole('button', { name: 'View' }));

    expect(document.querySelectorAll('aside.fixed.right-0')).toHaveLength(1);
    expect(within(getDetailPanel()!).getByRole('heading', { name: 'Beta Mortgage', level: 2 })).toBeInTheDocument();
    expect(within(getDetailPanel()!).getByText('Mortgage')).toHaveClass('bg-green-100');
    expect(within(getDetailPanel()!).queryByRole('heading', { name: 'Alpha Retirement', level: 2 })).toBeNull();
  });

  it('opens from grid card click and returns to grid after close', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();

    const taxCard = getScenarioCards().find((card) =>
      within(card).queryByRole('heading', { name: 'Gamma Tax', level: 3 }),
    );
    expect(taxCard).toBeDefined();

    await user.click(taxCard!);
    expect(within(getDetailPanel()!).getByRole('heading', { name: 'Gamma Tax', level: 2 })).toBeInTheDocument();
    expect(within(getDetailPanel()!).getByText('Tax')).toHaveClass('bg-orange-100');
    expect(within(getDetailPanel()!).getByText('Gross Income')).toBeInTheDocument();
    expect(within(getDetailPanel()!).getByText('Estimated Tax')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Close detail panel' }));
    expect(getDetailPanel()).toBeNull();
    expect(getScenarioCards()).toHaveLength(3);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
