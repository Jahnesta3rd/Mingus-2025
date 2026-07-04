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

const VIEW_MODE_KEY = 'scenario_view_mode';

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

function getFirstListRow(): HTMLElement {
  const table = screen.getByRole('table');
  return within(table).getAllByRole('row')[1];
}

function getScenarioCards(): HTMLElement[] {
  return screen
    .queryAllByRole('heading', { level: 3 })
    .map((heading) => heading.closest('article'))
    .filter((card): card is HTMLElement => card !== null);
}

describe('ScenarioManagement view modes', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedScenarios();
  });

  it('defaults to list view with a table', () => {
    renderDashboard();

    expect(screen.getByRole('button', { name: 'List View' })).toHaveClass('bg-blue-600');
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(getScenarioCards()).toHaveLength(0);
  });

  it('renders list view columns, rows, actions, and hover styling', () => {
    renderDashboard();

    expect(screen.getByRole('button', { name: 'Scenario Name' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Calculator Type' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Date Created' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Last Modified/ })).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();

    const row = getFirstListRow();
    expect(row).toHaveClass('hover:bg-gray-50');
    expect(within(row).getByRole('button', { name: 'View' })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Duplicate' })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Rename' })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Export' })).toBeInTheDocument();

    const table = screen.getByRole('table');
    expect(within(table).getAllByRole('row')).toHaveLength(4);
  });

  it('switches to grid view with cards', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(screen.getByRole('button', { name: 'Grid View' }));

    expect(screen.getByRole('button', { name: 'Grid View' })).toHaveClass('bg-blue-600');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();

    const cards = getScenarioCards();
    expect(cards).toHaveLength(3);

    const firstCard = cards[0];
    expect(within(firstCard).getByRole('heading', { name: 'Gamma Tax' })).toBeInTheDocument();
    expect(within(firstCard).getByText('Tax')).toHaveClass('bg-orange-100', 'text-orange-800');
    expect(within(firstCard).getByText(/Created:/)).toBeInTheDocument();
    expect(within(firstCard).getByText(/Modified:/)).toBeInTheDocument();
    expect(within(firstCard).getByRole('button', { name: 'View' })).toBeInTheDocument();
    expect(within(firstCard).getByRole('button', { name: 'Duplicate' })).toBeInTheDocument();
    expect(within(firstCard).getByRole('button', { name: 'Rename' })).toBeInTheDocument();
    expect(within(firstCard).getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    expect(within(firstCard).getByRole('button', { name: 'Export' })).toBeInTheDocument();

    const grid = firstCard.parentElement;
    expect(grid).toHaveClass('xl:grid-cols-3');
  });

  it('switches back to list view from grid view', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'List View' }));
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(getScenarioCards()).toHaveLength(0);
  });

  it('persists grid view preference across remount', async () => {
    const user = userEvent.setup();
    const first = renderDashboard();

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(window.localStorage.getItem(VIEW_MODE_KEY)).toBe(JSON.stringify('grid'));

    first.unmount();
    renderDashboard();

    expect(screen.getByRole('button', { name: 'Grid View' })).toHaveClass('bg-blue-600');
    expect(getScenarioCards()).toHaveLength(3);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('persists list view preference across remount', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(VIEW_MODE_KEY, JSON.stringify('grid'));

    const first = renderDashboard();
    await user.click(screen.getByRole('button', { name: 'List View' }));
    expect(window.localStorage.getItem(VIEW_MODE_KEY)).toBe(JSON.stringify('list'));

    first.unmount();
    renderDashboard();

    expect(screen.getByRole('button', { name: 'List View' })).toHaveClass('bg-blue-600');
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('opens detail panel from action buttons in both views', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(within(getFirstListRow()).getByRole('button', { name: 'View' }));
    expect(screen.getByRole('heading', { name: 'Gamma Tax', level: 2 })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Close detail panel' }));

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    const card = getScenarioCards()[0];
    await user.click(within(card).getByRole('button', { name: 'View' }));
    expect(screen.getByRole('heading', { name: 'Gamma Tax', level: 2 })).toBeInTheDocument();
  });

  it('opens rename modal from action buttons in both views', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(within(getFirstListRow()).getByRole('button', { name: 'Rename' }));
    expect(screen.getByRole('heading', { name: 'Rename scenario' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Close modal' }));

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    const card = getScenarioCards()[0];
    await user.click(within(card).getByRole('button', { name: 'Rename' }));
    expect(screen.getByRole('heading', { name: 'Rename scenario' })).toBeInTheDocument();
  });
});
