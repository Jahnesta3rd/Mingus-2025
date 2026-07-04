import { TextEncoder, TextDecoder } from 'util';

Object.assign(global, { TextEncoder, TextDecoder });

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    output: jest.fn(() => new Blob(['%PDF'], { type: 'application/pdf' })),
    save: jest.fn(),
  })),
}));

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImportModal from '../ImportModal';
import {
  createBackup,
  exportScenariosAsCSV,
  exportScenariosAsJSON,
} from '../../utils/exportUtils';
import {
  loadScenarios,
  SCENARIO_STORAGE_KEY,
  type Scenario,
} from '../../utils/scenarioStorage';

const sampleScenarios: Scenario[] = [
  {
    scenario_id: 'sc_import_1',
    calculator_type: 'retirement',
    name: 'Test Retirement, Plan A',
    inputs: { age: 45, savings: 150000 },
    outputs: { years: 20, total: 390000 },
    notes: 'Sample',
    created_at: '2026-07-01T14:30:00.000Z',
    last_modified: '2026-07-04T10:00:00.000Z',
  },
  {
    scenario_id: 'sc_import_2',
    calculator_type: 'mortgage',
    name: 'Home Purchase',
    inputs: { homePrice: 450000 },
    outputs: { monthlyPayment: 2100 },
    notes: '',
    created_at: '2026-06-15T09:00:00.000Z',
    last_modified: '2026-06-20T12:00:00.000Z',
  },
  {
    scenario_id: 'sc_import_3',
    calculator_type: 'tax',
    name: 'Tax Estimate 2026',
    inputs: { grossIncome: 120000 },
    outputs: { estimatedTax: 22000 },
    notes: '',
    created_at: '2026-05-01T08:00:00.000Z',
    last_modified: '2026-05-01T08:00:00.000Z',
  },
];

describe('ImportModal integration', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('shows three tabs when open', () => {
    render(<ImportModal isOpen onClose={jest.fn()} onImportComplete={jest.fn()} />);

    expect(screen.getByText('Import Scenarios')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Backup Restore' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'CSV Import' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'JSON Import' })).toBeInTheDocument();
  });

  it('shows empty backup message when no backups exist', () => {
    render(<ImportModal isOpen onClose={jest.fn()} onImportComplete={jest.fn()} />);

    expect(
      screen.getByText('No backups available yet. Use bulk export to create one.'),
    ).toBeInTheDocument();
  });

  it('restores scenarios from backup after confirmation', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(sampleScenarios));
    createBackup();
    window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify([]));

    const onImportComplete = jest.fn();
    const onClose = jest.fn();

    render(
      <ImportModal isOpen onClose={onClose} onImportComplete={onImportComplete} />,
    );

    expect(screen.getByText(/3 scenarios/)).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: 'Restore' })[0]);
    expect(screen.getByText('Restore backup')).toBeInTheDocument();
    expect(
      screen.getByText(/Restore 3 scenarios from .+\? This will replace current scenarios\./),
    ).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: 'Restore' })[1]);

    expect(onImportComplete).toHaveBeenCalledWith(3);
    expect(onClose).toHaveBeenCalled();
    expect(loadScenarios()).toHaveLength(3);
  });

  it('imports valid CSV file with preview and validation', async () => {
    const user = userEvent.setup();
    const csvContent = exportScenariosAsCSV(sampleScenarios);
    const onImportComplete = jest.fn();
    const onClose = jest.fn();

    render(
      <ImportModal isOpen onClose={onClose} onImportComplete={onImportComplete} />,
    );

    await user.click(screen.getByRole('button', { name: 'CSV Import' }));

    const fileInput = document.getElementById('csv-file-input') as HTMLInputElement;
    const csvFile = new File([csvContent], 'scenarios_2026-07-04.csv', { type: 'text/csv' });
    Object.defineProperty(csvFile, 'text', {
      value: () => Promise.resolve(csvContent),
    });
    await user.upload(fileInput, csvFile);

    expect(screen.getByText('scenarios_2026-07-04.csv')).toBeInTheDocument();
    expect(screen.getByText('✓ Valid CSV format (3 scenarios)')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Scenario Name' })).toBeInTheDocument();
    expect(screen.getByText('Test Retirement, Plan A')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Import' }));

    expect(onImportComplete).toHaveBeenCalledWith(3);
    expect(onClose).toHaveBeenCalled();
    expect(loadScenarios()).toHaveLength(3);
    expect(loadScenarios()[0].name).toBe('Test Retirement, Plan A');
  });

  it('imports valid JSON pasted into textarea', async () => {
    const user = userEvent.setup();
    const jsonContent = exportScenariosAsJSON(sampleScenarios);
    const onImportComplete = jest.fn();
    const onClose = jest.fn();

    render(
      <ImportModal isOpen onClose={onClose} onImportComplete={onImportComplete} />,
    );

    await user.click(screen.getByRole('button', { name: 'JSON Import' }));
    fireEvent.change(screen.getByLabelText('Paste JSON here'), {
      target: { value: jsonContent },
    });

    expect(screen.getByText('✓ Valid JSON (3 scenarios)')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Import' }));

    expect(onImportComplete).toHaveBeenCalledWith(3);
    expect(onClose).toHaveBeenCalled();
    expect(loadScenarios()).toHaveLength(3);
  });

  it('shows CSV validation error for invalid format', async () => {
    const user = userEvent.setup();

    render(<ImportModal isOpen onClose={jest.fn()} onImportComplete={jest.fn()} />);

    await user.click(screen.getByRole('button', { name: 'CSV Import' }));

    const fileInput = document.getElementById('csv-file-input') as HTMLInputElement;
    const badCsv = new File(['name,type\nOnly,Two,Columns'], 'bad.csv', { type: 'text/csv' });
    await user.upload(fileInput, badCsv);

    expect(screen.getByText(/✗ Invalid CSV:/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Import' })).toBeDisabled();
    expect(loadScenarios()).toHaveLength(0);
  });

  it('shows JSON validation error for invalid syntax', async () => {
    const user = userEvent.setup();

    render(<ImportModal isOpen onClose={jest.fn()} onImportComplete={jest.fn()} />);

    await user.click(screen.getByRole('button', { name: 'JSON Import' }));
    fireEvent.change(screen.getByLabelText('Paste JSON here'), {
      target: { value: '{not valid json' },
    });

    expect(screen.getByText(/✗ Invalid JSON:/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Import' })).toBeDisabled();
    expect(loadScenarios()).toHaveLength(0);
  });
});
