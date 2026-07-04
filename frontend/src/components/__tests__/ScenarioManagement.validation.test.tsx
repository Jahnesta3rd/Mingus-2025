import React from 'react';
import { render, screen } from '@testing-library/react';
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

const SEED: Scenario[] = [
  {
    scenario_id: 'sc_one',
    calculator_type: 'retirement',
    name: 'Validation Retirement',
    inputs: { currentAge: 35 },
    outputs: { projectedSavings: 100000 },
    notes: '',
    created_at: '2026-07-04T10:00:00.000Z',
    last_modified: '2026-07-04T10:00:00.000Z',
  },
];

describe('ScenarioManagement full validation gaps', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(SEED));
  });

  it('duplicates with default "- Copy" suffix', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: 'Duplicate' }));
    expect(screen.getByLabelText('Scenario name')).toHaveValue('Validation Retirement - Copy');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(screen.getByText('Validation Retirement - Copy')).toBeInTheDocument();
  });

  it('rename keeps total stats unchanged', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    const totalBefore = screen.getByText('Total Scenarios').nextElementSibling?.textContent;
    await user.click(screen.getByRole('button', { name: 'Rename' }));
    await user.clear(screen.getByLabelText('Scenario name'));
    await user.type(screen.getByLabelText('Scenario name'), 'Renamed Scenario');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(screen.getByText('Total Scenarios').nextElementSibling).toHaveTextContent(totalBefore ?? '1');
    expect(screen.getByText('Retirement Plans').nextElementSibling).toHaveTextContent('1');
  });

  it('uses responsive layout classes for sidebar and grid', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    expect(document.querySelector('aside.hidden.lg\\:block')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Show Filters & Sort' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Grid View' }));
    expect(document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3')).toBeTruthy();
  });

  it('writes all localStorage preference keys', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getAllByLabelText('Filter by Type')[0], 'retirement');
    await user.selectOptions(screen.getAllByLabelText('Sort by')[0], 'alpha-asc');
    await user.click(screen.getByRole('button', { name: 'Grid View' }));

    expect(window.localStorage.getItem(FILTER_STATE_KEY)).toContain('"type":"retirement"');
    expect(window.localStorage.getItem(SORT_KEY)).toBe(JSON.stringify('alpha-asc'));
    expect(window.localStorage.getItem(VIEW_MODE_KEY)).toBe(JSON.stringify('grid'));
  });
});
