import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import { saveScenario } from '../../utils/scenarioStorage';

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  })),
}));

function localDateYmd(offsetDays = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function seedTestScenarios(): void {
  saveScenario({
    calculator_type: 'retirement',
    name: 'Test Retirement',
    inputs: { currentAge: 35, retirementAge: 65 },
    outputs: { projectedSavings: 500000 },
    notes: '',
  });
  saveScenario({
    calculator_type: 'mortgage',
    name: 'Test Mortgage',
    inputs: { homePrice: 400000, downPayment: 80000 },
    outputs: { monthlyPayment: 2100 },
    notes: '',
  });
  saveScenario({
    calculator_type: 'tax',
    name: 'Test Tax',
    inputs: { grossIncome: 100000, deductions: 15000 },
    outputs: { estimatedTax: 18700 },
    notes: '',
  });
}

function getFilterControl<T extends HTMLElement>(
  label: string,
  role: 'combobox' | 'textbox' | 'label' = 'combobox',
): T {
  if (role === 'label') {
    return screen.getAllByLabelText(label)[0] as T;
  }
  const matches = screen.getAllByRole(role, { name: label });
  return matches[0] as T;
}

function expectScenarioNames(names: string[]): void {
  const table = screen.getByRole('table');
  const rows = within(table).getAllByRole('row').slice(1);
  expect(rows).toHaveLength(names.length);
  const actual = rows.map((row) => within(row).getAllByRole('cell')[1].textContent ?? '');
  expect(actual.sort()).toEqual([...names].sort());
}

describe('ScenarioManagement filtering and search', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedTestScenarios();
  });

  it('shows all three seeded scenarios on load', () => {
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('Test Retirement')).toBeInTheDocument();
    expect(screen.getByText('Test Mortgage')).toBeInTheDocument();
    expect(screen.getByText('Test Tax')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('filters by calculator type', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    const typeFilter = getFilterControl<HTMLSelectElement>('Filter by Type');
    await user.selectOptions(typeFilter, 'retirement');
    expectScenarioNames(['Test Retirement']);

    await user.selectOptions(typeFilter, 'mortgage');
    expectScenarioNames(['Test Mortgage']);

    await user.selectOptions(typeFilter, 'all');
    expectScenarioNames(['Test Retirement', 'Test Mortgage', 'Test Tax']);
  });

  it('filters by search text', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    const searchInput = getFilterControl<HTMLInputElement>('Search', 'textbox');
    await user.type(searchInput, 'Retirement');
    expectScenarioNames(['Test Retirement']);

    await user.clear(searchInput);
    expectScenarioNames(['Test Retirement', 'Test Mortgage', 'Test Tax']);
  });

  it('filters by date range', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    const fromInput = getFilterControl<HTMLInputElement>('From', 'label');
    await user.type(fromInput, localDateYmd(0));
    expectScenarioNames(['Test Retirement', 'Test Mortgage', 'Test Tax']);

    await user.clear(fromInput);
    await user.type(fromInput, localDateYmd(1));
    expect(
      screen.getByText('No scenarios saved yet. Go to calculators to create one.'),
    ).toBeInTheDocument();

    await user.clear(fromInput);
    expectScenarioNames(['Test Retirement', 'Test Mortgage', 'Test Tax']);
  });

  it('combines type and search filters with AND logic', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    const typeFilter = getFilterControl<HTMLSelectElement>('Filter by Type');
    const searchInput = getFilterControl<HTMLInputElement>('Search', 'textbox');

    await user.selectOptions(typeFilter, 'retirement');
    await user.type(searchInput, 'Test');
    expectScenarioNames(['Test Retirement']);

    await user.click(screen.getAllByRole('button', { name: 'Clear Filters' })[0]);
    expectScenarioNames(['Test Retirement', 'Test Mortgage', 'Test Tax']);
  });
});
