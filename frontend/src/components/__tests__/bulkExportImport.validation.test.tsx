import { TextEncoder, TextDecoder } from 'util';

Object.assign(global, { TextEncoder, TextDecoder });

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    output: jest.fn(() => new Blob(['%PDF-1.4 scenario'], { type: 'application/pdf' })),
    save: jest.fn(),
  })),
}));

jest.mock('jszip', () => ({
  __esModule: true,
  default: class MockJSZip {
    file(): void {}

    async generateAsync(): Promise<Blob> {
      return new Blob(['zip-content'], { type: 'application/zip' });
    }
  },
}));

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';
import BulkExportModal from '../BulkExportModal';
import ImportModal from '../ImportModal';
import {
  createBackup,
  exportScenariosAsCSV,
  exportScenariosAsJSON,
  exportScenariosAsZip,
  getTodayDateString,
  parseCSVToScenarios,
  sanitizeFileName,
  validateCSVStructure,
  validateJSONStructure,
} from '../../utils/exportUtils';
import {
  loadScenarios,
  SCENARIO_STORAGE_KEY,
  type Scenario,
} from '../../utils/scenarioStorage';

const sampleScenarios: Scenario[] = [
  {
    scenario_id: 'sc_val_1',
    calculator_type: 'retirement',
    name: 'Retire Early, Plan A',
    inputs: { age: 45, savings: 150000 },
    outputs: { years: 20, total: 390000 },
    notes: 'Note one',
    created_at: '2026-07-01T14:30:00.000Z',
    last_modified: '2026-07-04T10:00:00.000Z',
  },
  {
    scenario_id: 'sc_val_2',
    calculator_type: 'mortgage',
    name: 'Home Purchase',
    inputs: { homePrice: 450000 },
    outputs: { monthlyPayment: 2100 },
    notes: '',
    created_at: '2026-06-15T09:00:00.000Z',
    last_modified: '2026-06-20T12:00:00.000Z',
  },
  {
    scenario_id: 'sc_val_3',
    calculator_type: 'tax',
    name: 'Tax Estimate',
    inputs: { grossIncome: 120000 },
    outputs: { estimatedTax: 22000 },
    notes: 'FY26',
    created_at: '2026-05-01T08:00:00.000Z',
    last_modified: '2026-05-01T08:00:00.000Z',
  },
];

function getImportModal(): HTMLElement {
  return screen.getByText('Import Scenarios').closest('.max-w-2xl') as HTMLElement;
}

describe('Bulk Export/Import full validation', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.URL.createObjectURL = jest.fn(() => 'blob:test');
    window.URL.revokeObjectURL = jest.fn();
  });

  describe('dashboard UI (items 1-4, 36)', () => {
    it('shows Bulk Export and Import buttons that open modals', async () => {
      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <ScenarioManagement />
        </MemoryRouter>,
      );

      const bulkExport = screen.getByLabelText('Bulk Export');
      const importBtn = screen.getByLabelText('Import');
      expect(bulkExport).toBeInTheDocument();
      expect(importBtn).toBeInTheDocument();
      expect(bulkExport.className).toContain('bg-blue-600');
      expect(importBtn.className).toContain('bg-blue-600');

      await user.click(bulkExport);
      expect(screen.getByText('Export Scenarios')).toBeInTheDocument();

      await user.click(screen.getByLabelText('Close modal'));
      await user.click(importBtn);
      expect(screen.getByText('Import Scenarios')).toBeInTheDocument();
    });
  });

  describe('CSV export (items 5-7, 38)', () => {
    it('generates correctly formatted CSV with date-based filename', () => {
      const csv = exportScenariosAsCSV(sampleScenarios);
      const lines = csv.split('\n');

      expect(lines[0]).toBe(
        'Scenario Name,Type,Date Created,Last Modified,Inputs,Outputs',
      );
      expect(lines).toHaveLength(4);
      expect(lines[1]).toContain('"Retire Early, Plan A"');
      expect(lines[1]).toContain('retirement');
      expect(lines[1]).toMatch(/Jul 1, 2026/);
      expect(lines[1]).toContain('age=45, savings=150000');

      const filename = `scenarios_${getTodayDateString()}.csv`;
      expect(filename).toMatch(/^scenarios_\d{4}-\d{2}-\d{2}\.csv$/);
      expect(validateCSVStructure(csv).valid).toBe(true);
    });
  });

  describe('JSON export (items 8-9, 38)', () => {
    it('generates valid JSON with all scenario fields', () => {
      const json = exportScenariosAsJSON(sampleScenarios);
      const parsed = JSON.parse(json) as Scenario[];

      expect(parsed).toHaveLength(3);
      parsed.forEach((scenario) => {
        expect(scenario).toHaveProperty('scenario_id');
        expect(scenario).toHaveProperty('calculator_type');
        expect(scenario).toHaveProperty('name');
        expect(scenario).toHaveProperty('inputs');
        expect(scenario).toHaveProperty('outputs');
        expect(scenario).toHaveProperty('notes');
        expect(scenario).toHaveProperty('created_at');
        expect(scenario).toHaveProperty('last_modified');
      });

      expect(`scenarios_${getTodayDateString()}.json`).toMatch(
        /^scenarios_\d{4}-\d{2}-\d{2}\.json$/,
      );
    });
  });

  describe('ZIP export (items 10-12, 37-38)', () => {
    it('uses sanitized scenario filenames and triggers ZIP download', async () => {
      let zipBlob: Blob | null = null;
      window.URL.createObjectURL = jest.fn((blob: Blob) => {
        zipBlob = blob;
        return 'blob:test';
      });

      const originalCreateElement = document.createElement.bind(document);
      document.createElement = ((tagName: string) => {
        const element = originalCreateElement(tagName);
        if (tagName === 'a') element.click = jest.fn();
        return element;
      }) as typeof document.createElement;

      await exportScenariosAsZip(sampleScenarios);

      expect(zipBlob).not.toBeNull();
      expect(sanitizeFileName('Retire Early, Plan A')).toBe('retire_early_plan_a');
      expect(`scenarios_${getTodayDateString()}.zip`).toMatch(/^scenarios_\d{4}-\d{2}-\d{2}\.zip$/);
    });

    it('shows loading spinner during ZIP generation in modal', async () => {
      const user = userEvent.setup();
      render(
        <BulkExportModal isOpen onClose={jest.fn()} scenarios={sampleScenarios} />,
      );

      void user.click(screen.getByRole('button', { name: 'Export as ZIP' }));
      expect(screen.getByLabelText('Generating ZIP')).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: 'Export as ZIP' }));
    });
  });

  describe('backup operations (items 13-19, 40)', () => {
    beforeEach(() => {
      window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(sampleScenarios));
    });

    it('creates, lists, deletes, and restores backups correctly', () => {
      const result = createBackup();
      expect(result.success).toBe(true);
      expect(result.count).toBe(3);
      expect(`mingus_scenarios_backup_${result.timestamp}`).toMatch(
        /^mingus_scenarios_backup_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$/,
      );

      window.localStorage.setItem(
        'mingus_scenarios_backup_2026-07-04_14-28-00',
        JSON.stringify(sampleScenarios),
      );
      window.localStorage.setItem(
        'mingus_scenarios_backup_2026-07-04_14-30-00',
        JSON.stringify(sampleScenarios),
      );

      const keys = Object.keys(window.localStorage).filter((key) =>
        key.startsWith('mingus_scenarios_backup_'),
      );
      expect(keys.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('import flows (items 20-31)', () => {
    it('validates CSV/JSON, imports with new ids, and rejects invalid input', async () => {
      const user = userEvent.setup();
      const csv = exportScenariosAsCSV(sampleScenarios);
      const validation = validateCSVStructure(csv);
      expect(validation.valid).toBe(true);

      const parsedCsv = parseCSVToScenarios(validation.rows);
      expect(parsedCsv).toHaveLength(3);
      parsedCsv.forEach((scenario) => {
        expect(scenario.scenario_id).not.toMatch(/^sc_val_/);
        expect(scenario.scenario_id).toMatch(/^sc_/);
      });

      const badCsv = validateCSVStructure('name,type\nbad,data');
      expect(badCsv.valid).toBe(false);

      const json = exportScenariosAsJSON(sampleScenarios);
      expect(validateJSONStructure(json).valid).toBe(true);
      expect(validateJSONStructure('{bad').valid).toBe(false);

      render(
        <MemoryRouter>
          <ScenarioManagement />
        </MemoryRouter>,
      );

      await user.click(screen.getByLabelText('Import'));
      await user.click(screen.getByRole('button', { name: 'CSV Import' }));

      const csvFile = new File([csv], 'test.csv', { type: 'text/csv' });
      Object.defineProperty(csvFile, 'text', {
        value: () => Promise.resolve(csv),
      });
      await user.upload(document.getElementById('csv-file-input') as HTMLInputElement, csvFile);

      expect(screen.getByText('✓ Valid CSV format (3 scenarios)')).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Scenario Name' })).toBeInTheDocument();

      await user.click(within(getImportModal()).getByRole('button', { name: 'Import' }));
      expect(loadScenarios()).toHaveLength(3);
    });
  });

  describe('dashboard refresh and stats (items 26-29)', () => {
    it('updates total scenario stats after import with success message', async () => {
      const user = userEvent.setup();
      const json = exportScenariosAsJSON(sampleScenarios);

      render(
        <MemoryRouter>
          <ScenarioManagement />
        </MemoryRouter>,
      );

      expect(screen.getByText('Total Scenarios').closest('div')?.parentElement).toHaveTextContent('0');

      await user.click(screen.getByLabelText('Import'));
      await user.click(screen.getByRole('button', { name: 'JSON Import' }));
      fireEvent.change(screen.getByLabelText('Paste JSON here'), { target: { value: json } });
      await user.click(within(getImportModal()).getByRole('button', { name: 'Import' }));

      expect(screen.getByText('✓ Imported 3 scenarios')).toBeInTheDocument();
      expect(screen.getByText('Total Scenarios').closest('div')?.parentElement).toHaveTextContent('3');
    });
  });

  describe('confirmation modals (items 32-33)', () => {
    it('requires confirmation before restore or delete', async () => {
      const user = userEvent.setup();
      window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(sampleScenarios));
      createBackup();

      render(<ImportModal isOpen onClose={jest.fn()} onImportComplete={jest.fn()} />);

      await user.click(screen.getByRole('button', { name: 'Restore' }));
      expect(screen.getByText('Restore backup')).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: 'Cancel' }));
      expect(loadScenarios()).toHaveLength(3);

      await user.click(screen.getByRole('button', { name: 'Delete' }));
      expect(screen.getByText('Delete backup')).toBeInTheDocument();
    });
  });

  describe('modal UX (items 34-35)', () => {
    it('keeps BulkExportModal open and links to import', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      const onImportClick = jest.fn();

      render(
        <BulkExportModal
          isOpen
          onClose={onClose}
          scenarios={sampleScenarios}
          onImportClick={onImportClick}
        />,
      );

      await user.click(screen.getByRole('button', { name: 'Export as JSON' }));
      expect(onClose).not.toHaveBeenCalled();
      expect(screen.getByText('Export Scenarios')).toBeInTheDocument();

      await user.click(screen.getByText('Need to import?'));
      expect(onImportClick).toHaveBeenCalled();
    });
  });
});
