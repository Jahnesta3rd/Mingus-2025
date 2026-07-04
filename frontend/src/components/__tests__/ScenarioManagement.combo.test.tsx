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

const FILTER_STATE_KEY = 'scenario_filter_state';
const SORT_KEY = 'scenario_sort';
const VIEW_MODE_KEY = 'scenario_view_mode';

function localDateYmd(offsetDays = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

const TODAY = localDateYmd(0);

const SEED_SCENARIOS: Scenario[] = [
  {
    scenario_id: 'sc_ret_zulu',
    calculator_type: 'retirement',
    name: 'Zulu Retirement',
    inputs: { currentAge: 40 },
    outputs: { projectedSavings: 400000 },
    notes: '',
    created_at: `${TODAY}T12:00:00.000Z`,
    last_modified: `${TODAY}T12:00:00.000Z`,
  },
  {
    scenario_id: 'sc_ret_alpha',
    calculator_type: 'retirement',
    name: 'Alpha Retirement',
    inputs: { currentAge: 35 },
    outputs: { projectedSavings: 500000 },
    notes: '',
    created_at: `${TODAY}T10:00:00.000Z`,
    last_modified: `${TODAY}T10:00:00.000Z`,
  },
  {
    scenario_id: 'sc_mort_old',
    calculator_type: 'mortgage',
    name: 'Test Mortgage Old',
    inputs: { homePrice: 300000 },
    outputs: { monthlyPayment: 1800 },
    notes: '',
    created_at: `${TODAY}T08:00:00.000Z`,
    last_modified: `${TODAY}T08:00:00.000Z`,
  },
  {
    scenario_id: 'sc_mort_new',
    calculator_type: 'mortgage',
    name: 'Test Mortgage New',
    inputs: { homePrice: 350000 },
    outputs: { monthlyPayment: 2000 },
    notes: '',
    created_at: `${TODAY}T14:00:00.000Z`,
    last_modified: `${TODAY}T14:00:00.000Z`,
  },
  {
    scenario_id: 'sc_tax_test',
    calculator_type: 'tax',
    name: 'Test Tax',
    inputs: { grossIncome: 90000 },
    outputs: { estimatedTax: 15000 },
    notes: '',
    created_at: `${TODAY}T09:00:00.000Z`,
    last_modified: `${TODAY}T09:00:00.000Z`,
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

function getFilterControl<T extends HTMLElement>(
  label: string,
  role: 'combobox' | 'textbox' | 'label' = 'combobox',
): T {
  if (role === 'label') {
    return screen.getAllByLabelText(label)[0] as T;
  }
  return screen.getAllByRole(role, { name: label })[0] as T;
}

function getListRowNamesInOrder(): string[] {
  const table = screen.getByRole('table');
  return within(table)
    .getAllByRole('row')
    .slice(1)
    .map((row) => within(row).getAllByRole('cell')[1].textContent ?? '');
}

function getCardNamesInOrder(): string[] {
  return screen.queryAllByRole('heading', { level: 3 }).map((heading) => heading.textContent ?? '');
}

describe('ScenarioManagement filter + sort + view combinations', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedScenarios();
  });

  it('filters by type then sorts alphabetically in list view', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getFilterControl('Filter by Type'), 'retirement');
    await user.selectOptions(getFilterControl('Sort by'), 'alpha-asc');

    expect(getListRowNamesInOrder()).toEqual(['Alpha Retirement', 'Zulu Retirement']);
  });

  it('keeps search applied when switching between list and grid views', async () => {
    const user = userEvent.setup();
    renderDashboard();

    const searchInput = getFilterControl<HTMLInputElement>('Search', 'textbox');
    await user.type(searchInput, 'Test');

    expect(getListRowNamesInOrder().sort()).toEqual(
      ['Test Mortgage New', 'Test Mortgage Old', 'Test Tax'].sort(),
    );

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(getCardNamesInOrder().sort()).toEqual(
      ['Test Mortgage New', 'Test Mortgage Old', 'Test Tax'].sort(),
    );
    expect(searchInput).toHaveValue('Test');

    await user.click(screen.getByRole('button', { name: 'List View' }));
    expect(getListRowNamesInOrder().sort()).toEqual(
      ['Test Mortgage New', 'Test Mortgage Old', 'Test Tax'].sort(),
    );
    expect(searchInput).toHaveValue('Test');
  });

  it('applies multiple filters and sort consistently across view modes', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getFilterControl('Filter by Type'), 'mortgage');
    await user.type(getFilterControl<HTMLInputElement>('From', 'label'), TODAY);
    await user.type(getFilterControl<HTMLInputElement>('To', 'label'), TODAY);
    await user.selectOptions(getFilterControl('Sort by'), 'oldest');

    expect(getListRowNamesInOrder()).toEqual(['Test Mortgage Old', 'Test Mortgage New']);

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(getCardNamesInOrder()).toEqual(['Test Mortgage Old', 'Test Mortgage New']);

    await user.click(screen.getByRole('button', { name: 'List View' }));
    expect(getListRowNamesInOrder()).toEqual(['Test Mortgage Old', 'Test Mortgage New']);
  });

  it('clears filters but leaves sort unchanged', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.selectOptions(getFilterControl('Filter by Type'), 'retirement');
    await user.type(getFilterControl<HTMLInputElement>('From', 'label'), TODAY);
    await user.type(getFilterControl<HTMLInputElement>('Search', 'textbox'), 'Alpha');
    await user.selectOptions(getFilterControl('Sort by'), 'alpha-asc');

    expect(getListRowNamesInOrder()).toEqual(['Alpha Retirement']);

    await user.click(screen.getAllByRole('button', { name: 'Clear Filters' })[0]);

    expect(getFilterControl<HTMLSelectElement>('Filter by Type')).toHaveValue('all');
    expect(getFilterControl<HTMLInputElement>('From', 'label')).toHaveValue('');
    expect(getFilterControl<HTMLInputElement>('To', 'label')).toHaveValue('');
    expect(getFilterControl<HTMLInputElement>('Search', 'textbox')).toHaveValue('');
    expect(getFilterControl<HTMLSelectElement>('Sort by')).toHaveValue('alpha-asc');
    expect(getListRowNamesInOrder()).toEqual([
      'Alpha Retirement',
      'Test Mortgage New',
      'Test Mortgage Old',
      'Test Tax',
      'Zulu Retirement',
    ]);
  });

  it('persists filters, sort, and view mode across remount', async () => {
    const user = userEvent.setup();
    const first = renderDashboard();

    await user.selectOptions(getFilterControl('Filter by Type'), 'retirement');
    await user.selectOptions(getFilterControl('Sort by'), 'alpha-asc');
    await user.click(screen.getByRole('button', { name: 'Grid View' }));

    expect(JSON.parse(window.localStorage.getItem(FILTER_STATE_KEY) ?? '{}')).toMatchObject({
      type: 'retirement',
    });
    expect(window.localStorage.getItem(SORT_KEY)).toBe(JSON.stringify('alpha-asc'));
    expect(window.localStorage.getItem(VIEW_MODE_KEY)).toBe(JSON.stringify('grid'));
    expect(getCardNamesInOrder()).toEqual(['Alpha Retirement', 'Zulu Retirement']);

    first.unmount();
    renderDashboard();

    expect(getFilterControl<HTMLSelectElement>('Filter by Type')).toHaveValue('retirement');
    expect(getFilterControl<HTMLSelectElement>('Sort by')).toHaveValue('alpha-asc');
    expect(screen.getByRole('button', { name: 'Grid View' })).toHaveClass('bg-blue-600');
    expect(getCardNamesInOrder()).toEqual(['Alpha Retirement', 'Zulu Retirement']);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
