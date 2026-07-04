import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import { loadScenarios, SCENARIO_STORAGE_KEY, type Scenario } from '../../utils/scenarioStorage';

const mockPdfSave = jest.fn();
const mockPdfText = jest.fn();

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: mockPdfText,
    save: mockPdfSave,
  })),
}));

const SEED_SCENARIOS: Scenario[] = [
  {
    scenario_id: 'sc_alpha',
    calculator_type: 'retirement',
    name: 'Alpha Retirement',
    inputs: { currentAge: 35, currentSavings: 85000 },
    outputs: { projectedSavings: 500000 },
    notes: 'Original notes',
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
  return Number(labelEl.nextElementSibling?.textContent ?? 0);
}

function getListRowByName(name: string): HTMLElement {
  const table = screen.getByRole('table');
  const row = within(table)
    .getAllByRole('row')
    .find((candidate) => within(candidate).queryByText(name));
  if (!row) throw new Error(`Row not found for ${name}`);
  return row;
}

function getScenarioCardByName(name: string): HTMLElement {
  const card = getScenarioCards().find((candidate) =>
    within(candidate).queryByRole('heading', { name, level: 3 }),
  );
  if (!card) throw new Error(`Card not found for ${name}`);
  return card;
}

function getScenarioCards(): HTMLElement[] {
  return screen
    .queryAllByRole('heading', { level: 3 })
    .map((heading) => heading.closest('article'))
    .filter((card): card is HTMLElement => card !== null);
}

function getModalConfirmDeleteButton(): HTMLElement {
  const button = screen
    .getAllByRole('button', { name: 'Delete' })
    .find((candidate) => candidate.className.includes('bg-red-600'));
  if (!button) throw new Error('Confirm delete button not found');
  return button;
}

async function switchToGridView(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  await user.click(screen.getByRole('button', { name: 'Grid View' }));
}

describe('ScenarioManagement dashboard actions', () => {
  beforeEach(() => {
    window.localStorage.clear();
    seedScenarios();
    mockPdfSave.mockClear();
    mockPdfText.mockClear();
  });

  describe('list view', () => {
    it('duplicates a scenario with a custom name and updates stats', async () => {
      const user = userEvent.setup();
      renderDashboard();

      expect(getStatValue('Total Scenarios')).toBe(3);

      await user.click(within(getListRowByName('Alpha Retirement')).getByRole('button', { name: 'Duplicate' }));
      expect(screen.getByRole('heading', { name: 'Duplicate scenario - enter new name' })).toBeInTheDocument();

      const nameInput = screen.getByLabelText('Scenario name');
      expect(nameInput).toHaveValue('Alpha Retirement - Copy');

      await user.clear(nameInput);
      await user.type(nameInput, 'Alpha Retirement - Variant');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      expect(screen.getByText('Alpha Retirement - Variant')).toBeInTheDocument();
      expect(screen.getByText('Scenario duplicated: Alpha Retirement - Variant')).toBeInTheDocument();
      expect(getStatValue('Total Scenarios')).toBe(4);
      expect(getStatValue('Retirement Plans')).toBe(2);
      expect(loadScenarios()).toHaveLength(4);
    });

    it('renames a scenario and updates the list', async () => {
      const user = userEvent.setup();
      renderDashboard();

      await user.click(within(getListRowByName('Beta Mortgage')).getByRole('button', { name: 'Rename' }));
      expect(screen.getByRole('heading', { name: 'Rename scenario' })).toBeInTheDocument();

      const nameInput = screen.getByLabelText('Scenario name');
      expect(nameInput).toHaveValue('Beta Mortgage');

      await user.clear(nameInput);
      await user.type(nameInput, 'My Updated Scenario');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      expect(screen.getByText('My Updated Scenario')).toBeInTheDocument();
      expect(screen.queryByText('Beta Mortgage')).not.toBeInTheDocument();
      expect(screen.getByText('Scenario renamed: My Updated Scenario')).toBeInTheDocument();
      expect(getStatValue('Total Scenarios')).toBe(3);
    });

    it('cancels delete and then confirms delete with updated stats', async () => {
      const user = userEvent.setup();
      renderDashboard();

      expect(getStatValue('Total Scenarios')).toBe(3);
      expect(getStatValue('Mortgage Plans')).toBe(1);

      await user.click(within(getListRowByName('Beta Mortgage')).getByRole('button', { name: 'Delete' }));
      expect(screen.getByText('Are you sure? This cannot be undone.')).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: 'Cancel' }));
      expect(screen.getByText('Beta Mortgage')).toBeInTheDocument();

      await user.click(within(getListRowByName('Beta Mortgage')).getByRole('button', { name: 'Delete' }));
      await user.click(getModalConfirmDeleteButton());

      expect(screen.queryByText('Beta Mortgage')).not.toBeInTheDocument();
      expect(screen.getByText('Scenario deleted.')).toBeInTheDocument();
      expect(getStatValue('Total Scenarios')).toBe(2);
      expect(getStatValue('Mortgage Plans')).toBe(0);
      expect(getStatValue('Retirement Plans')).toBe(1);
      expect(getStatValue('Tax Plans')).toBe(1);
    });

    it('exports a scenario as PDF with the expected filename and content', async () => {
      const user = userEvent.setup();
      renderDashboard();

      await user.click(within(getListRowByName('Alpha Retirement')).getByRole('button', { name: 'Export' }));

      expect(mockPdfSave).toHaveBeenCalledTimes(1);
      expect(mockPdfSave).toHaveBeenCalledWith('alpha_retirement_2026-07-01.pdf');
      expect(mockPdfText).toHaveBeenCalledWith('Scenario Export', 14, 18);
      expect(mockPdfText).toHaveBeenCalledWith('Scenario name: Alpha Retirement', 14, 30);
      expect(mockPdfText).toHaveBeenCalledWith('Type: retirement', 14, 38);
      expect(mockPdfText).toHaveBeenCalledWith('Inputs', 14, expect.any(Number));
      expect(mockPdfText).toHaveBeenCalledWith('Outputs', 14, expect.any(Number));
    });
  });

  describe('grid view', () => {
    it('duplicates a scenario from a card', async () => {
      const user = userEvent.setup();
      renderDashboard();
      await switchToGridView(user);

      await user.click(within(getScenarioCardByName('Alpha Retirement')).getByRole('button', { name: 'Duplicate' }));

      const nameInput = screen.getByLabelText('Scenario name');
      await user.clear(nameInput);
      await user.type(nameInput, 'Alpha Retirement - Variant');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      expect(screen.getByText('Alpha Retirement - Variant')).toBeInTheDocument();
      expect(getStatValue('Total Scenarios')).toBe(4);
    });

    it('renames a scenario from a card', async () => {
      const user = userEvent.setup();
      renderDashboard();
      await switchToGridView(user);

      await user.click(within(getScenarioCardByName('Beta Mortgage')).getByRole('button', { name: 'Rename' }));

      const nameInput = screen.getByLabelText('Scenario name');
      await user.clear(nameInput);
      await user.type(nameInput, 'My Updated Scenario');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      expect(screen.getByText('My Updated Scenario')).toBeInTheDocument();
    });

    it('deletes a scenario from a card after confirmation', async () => {
      const user = userEvent.setup();
      renderDashboard();
      await switchToGridView(user);

      await user.click(within(getScenarioCardByName('Beta Mortgage')).getByRole('button', { name: 'Delete' }));
      await user.click(getModalConfirmDeleteButton());

      expect(screen.queryByText('Beta Mortgage')).not.toBeInTheDocument();
      expect(getStatValue('Total Scenarios')).toBe(2);
      expect(getStatValue('Mortgage Plans')).toBe(0);
    });

    it('exports a scenario from a card', async () => {
      const user = userEvent.setup();
      renderDashboard();
      await switchToGridView(user);

      await user.click(within(getScenarioCardByName('Alpha Retirement')).getByRole('button', { name: 'Export' }));

      expect(mockPdfSave).toHaveBeenCalledWith('alpha_retirement_2026-07-01.pdf');
    });
  });
});
