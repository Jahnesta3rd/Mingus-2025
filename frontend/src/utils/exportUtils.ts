import jsPDF from 'jspdf';
import JSZip from 'jszip';
import {
  loadScenarios,
  SCENARIO_STORAGE_KEY,
  type Scenario,
} from './scenarioStorage';

export type { Scenario };

const BACKUP_KEY_PREFIX = 'mingus_scenarios_backup_';

const CSV_HEADERS = [
  'Scenario Name',
  'Type',
  'Date Created',
  'Last Modified',
  'Inputs',
  'Outputs',
] as const;

const REQUIRED_JSON_FIELDS: (keyof Scenario)[] = [
  'scenario_id',
  'calculator_type',
  'name',
  'inputs',
  'outputs',
  'notes',
  'created_at',
  'last_modified',
];

function canUseBrowserApis(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

function canUseLocalStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function createScenarioId(): string {
  return `sc_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function escapeCSVField(value: string): string {
  if (/[",\n\r]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function formatKeyValuePairs(record: Record<string, unknown>, limit: number): string {
  return Object.entries(record)
    .slice(0, limit)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(', ');
}

function parseKeyValueString(text: string): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  if (!text.trim()) {
    return result;
  }

  text.split(',').forEach((pair) => {
    const trimmed = pair.trim();
    const equalsIndex = trimmed.indexOf('=');
    if (equalsIndex === -1) {
      return;
    }

    const key = trimmed.slice(0, equalsIndex).trim();
    const valueText = trimmed.slice(equalsIndex + 1).trim();
    if (!key) {
      return;
    }

    if (/^-?\d+(\.\d+)?$/.test(valueText)) {
      result[key] = Number(valueText);
      return;
    }

    result[key] = valueText;
  });

  return result;
}

function parseCSVRows(csvText: string): string[][] {
  const rows: string[][] = [];
  let currentRow: string[] = [];
  let currentField = '';
  let inQuotes = false;

  for (let index = 0; index < csvText.length; index += 1) {
    const char = csvText[index];
    const nextChar = csvText[index + 1];

    if (inQuotes) {
      if (char === '"' && nextChar === '"') {
        currentField += '"';
        index += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        currentField += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === ',') {
      currentRow.push(currentField);
      currentField = '';
    } else if (char === '\n' || (char === '\r' && nextChar === '\n')) {
      currentRow.push(currentField);
      rows.push(currentRow);
      currentRow = [];
      currentField = '';
      if (char === '\r') {
        index += 1;
      }
    } else if (char === '\r') {
      currentRow.push(currentField);
      rows.push(currentRow);
      currentRow = [];
      currentField = '';
    } else {
      currentField += char;
    }
  }

  if (currentField.length > 0 || currentRow.length > 0) {
    currentRow.push(currentField);
    rows.push(currentRow);
  }

  return rows;
}

function normalizeHeader(header: string): string {
  return header.trim().toLowerCase();
}

function triggerDownload(blob: Blob, filename: string): void {
  if (!canUseBrowserApis()) {
    return;
  }

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function getBackupTimestamp(date = new Date()): string {
  const pad = (value: number): string => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}_${pad(date.getHours())}-${pad(date.getMinutes())}-${pad(date.getSeconds())}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isValidScenario(value: unknown): value is Scenario {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.scenario_id === 'string' &&
    typeof value.calculator_type === 'string' &&
    typeof value.name === 'string' &&
    isRecord(value.inputs) &&
    isRecord(value.outputs) &&
    typeof value.notes === 'string' &&
    typeof value.created_at === 'string' &&
    typeof value.last_modified === 'string'
  );
}

function cloneScenario(scenario: Scenario): Scenario {
  return JSON.parse(JSON.stringify(scenario)) as Scenario;
}

export function formatDateForCSV(isoDate: string): string {
  try {
    return new Date(isoDate).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return isoDate;
  }
}

export function getTodayDateString(date = new Date()): string {
  const pad = (value: number): string => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function sanitizeFileName(name: string): string {
  return (
    name
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '') || 'scenario'
  );
}

export function exportScenariosAsCSV(scenarios: Scenario[]): string {
  try {
    const headerRow = CSV_HEADERS.join(',');
    if (scenarios.length === 0) {
      return headerRow;
    }

    const dataRows = scenarios.map((scenario) => {
      const row = [
        scenario.name,
        scenario.calculator_type,
        formatDateForCSV(scenario.created_at),
        formatDateForCSV(scenario.last_modified),
        formatKeyValuePairs(scenario.inputs, 5),
        formatKeyValuePairs(scenario.outputs, 3),
      ];
      return row.map((field) => escapeCSVField(field)).join(',');
    });

    return [headerRow, ...dataRows].join('\n');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to export scenarios as CSV';
    throw new Error(message);
  }
}

export function downloadCSV(csvContent: string, filename: string): void {
  try {
    if (!canUseBrowserApis()) {
      throw new Error('Browser download APIs are unavailable');
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    triggerDownload(blob, filename);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download CSV file';
    throw new Error(message);
  }
}

function generateScenarioPdfBlob(scenario: Scenario): Blob {
  const pdf = new jsPDF();
  let y = 18;

  const addLine = (label: string, value: string): void => {
    pdf.text(`${label}: ${value}`, 14, y);
    y += 8;
  };

  pdf.setFontSize(18);
  pdf.text('Scenario Export', 14, y);
  y += 12;

  pdf.setFontSize(11);
  addLine('Scenario name', scenario.name);
  addLine('Type', scenario.calculator_type);
  addLine('Date created', formatDateForCSV(scenario.created_at));
  addLine('Last modified', formatDateForCSV(scenario.last_modified));
  addLine('Notes', scenario.notes || 'None');
  y += 4;

  pdf.setFontSize(14);
  pdf.text('Inputs', 14, y);
  y += 8;
  pdf.setFontSize(11);

  Object.entries(scenario.inputs).forEach(([key, value]) => {
    addLine(key, String(value));
  });

  y += 4;
  pdf.setFontSize(14);
  pdf.text('Outputs', 14, y);
  y += 8;
  pdf.setFontSize(11);

  Object.entries(scenario.outputs).forEach(([key, value]) => {
    addLine(key, String(value));
  });

  return pdf.output('blob');
}

export async function exportScenariosAsZip(scenarios: Scenario[]): Promise<void> {
  try {
    if (!canUseBrowserApis()) {
      throw new Error('Browser download APIs are unavailable');
    }

    const zip = new JSZip();

    scenarios.forEach((scenario) => {
      const pdfBlob = generateScenarioPdfBlob(scenario);
      const datePart = scenario.created_at.slice(0, 10);
      const fileName = `${sanitizeFileName(scenario.name)}_${datePart}.pdf`;
      zip.file(fileName, pdfBlob);
    });

    const zipBlob = await zip.generateAsync({ type: 'blob' });
    downloadZip(zipBlob, `scenarios_${getTodayDateString()}.zip`);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to export scenarios as ZIP';
    throw new Error(message);
  }
}

export function downloadZip(zipBlob: Blob, filename: string): void {
  try {
    if (!canUseBrowserApis()) {
      throw new Error('Browser download APIs are unavailable');
    }

    triggerDownload(zipBlob, filename);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download ZIP file';
    throw new Error(message);
  }
}

export function exportScenariosAsJSON(scenarios: Scenario[]): string {
  try {
    const payload = scenarios.map((scenario) => cloneScenario(scenario));
    return JSON.stringify(payload, null, 2);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to export scenarios as JSON';
    throw new Error(message);
  }
}

export function downloadJSON(jsonContent: string, filename: string): void {
  try {
    if (!canUseBrowserApis()) {
      throw new Error('Browser download APIs are unavailable');
    }

    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    triggerDownload(blob, filename);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download JSON file';
    throw new Error(message);
  }
}

export function createBackup(): { timestamp: string; count: number; success: boolean } {
  const timestamp = getBackupTimestamp();

  try {
    if (!canUseLocalStorage()) {
      return { timestamp, count: 0, success: false };
    }

    const scenarios = loadScenarios();
    const backupKey = `${BACKUP_KEY_PREFIX}${timestamp}`;
    window.localStorage.setItem(backupKey, JSON.stringify(scenarios));

    return {
      timestamp,
      count: scenarios.length,
      success: true,
    };
  } catch {
    return { timestamp, count: 0, success: false };
  }
}

export function listBackups(): Array<{ timestamp: string; count: number; key: string }> {
  if (!canUseLocalStorage()) {
    return [];
  }

  try {
    const backups: Array<{ timestamp: string; count: number; key: string }> = [];

    for (let index = 0; index < window.localStorage.length; index += 1) {
      const key = window.localStorage.key(index);
      if (!key || !key.startsWith(BACKUP_KEY_PREFIX)) {
        continue;
      }

      const timestamp = key.slice(BACKUP_KEY_PREFIX.length);
      let count = 0;

      try {
        const raw = window.localStorage.getItem(key);
        if (raw) {
          const parsed = JSON.parse(raw) as unknown;
          count = Array.isArray(parsed) ? parsed.length : 0;
        }
      } catch {
        count = 0;
      }

      backups.push({ timestamp, count, key });
    }

    return backups.sort((left, right) => right.timestamp.localeCompare(left.timestamp));
  } catch {
    return [];
  }
}

export function restoreBackup(backupKey: string): {
  success: boolean;
  restored: number;
  errors: string[];
} {
  const errors: string[] = [];

  try {
    if (!canUseLocalStorage()) {
      return { success: false, restored: 0, errors: ['Local storage is unavailable'] };
    }

    if (!backupKey.startsWith(BACKUP_KEY_PREFIX)) {
      return { success: false, restored: 0, errors: ['Invalid backup key'] };
    }

    const raw = window.localStorage.getItem(backupKey);
    if (!raw) {
      return { success: false, restored: 0, errors: ['Backup not found'] };
    }

    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return { success: false, restored: 0, errors: ['Backup data is not a scenario array'] };
    }

    const validScenarios: Scenario[] = [];
    parsed.forEach((item, index) => {
      if (isValidScenario(item)) {
        validScenarios.push(cloneScenario(item));
        return;
      }
      errors.push(`Invalid scenario at index ${index}`);
    });

    window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(validScenarios));

    return {
      success: errors.length === 0,
      restored: validScenarios.length,
      errors,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to restore backup';
    return { success: false, restored: 0, errors: [message] };
  }
}

export function deleteBackup(backupKey: string): boolean {
  try {
    if (!canUseLocalStorage()) {
      return false;
    }

    if (!backupKey.startsWith(BACKUP_KEY_PREFIX)) {
      return false;
    }

    if (!window.localStorage.getItem(backupKey)) {
      return false;
    }

    window.localStorage.removeItem(backupKey);
    return true;
  } catch {
    return false;
  }
}

export function validateCSVStructure(csvText: string): {
  valid: boolean;
  errors: string[];
  rows: string[][];
} {
  const errors: string[] = [];

  try {
    const trimmed = csvText.trim();
    if (!trimmed) {
      return { valid: false, errors: ['CSV content is empty'], rows: [] };
    }

    const rows = parseCSVRows(trimmed);
    if (rows.length === 0) {
      return { valid: false, errors: ['CSV contains no rows'], rows: [] };
    }

    const headerRow = rows[0].map(normalizeHeader);
    const requiredHeaders = CSV_HEADERS.map(normalizeHeader);
    const missingHeaders = requiredHeaders.filter((header) => !headerRow.includes(header));

    if (missingHeaders.length > 0) {
      errors.push(`Missing required columns: ${missingHeaders.join(', ')}`);
      return { valid: false, errors, rows: [] };
    }

    return { valid: true, errors: [], rows };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to parse CSV';
    return { valid: false, errors: [message], rows: [] };
  }
}

export function validateJSONStructure(jsonText: string): {
  valid: boolean;
  errors: string[];
  data: Scenario[];
} {
  const errors: string[] = [];

  try {
    const trimmed = jsonText.trim();
    if (!trimmed) {
      return { valid: false, errors: ['JSON content is empty'], data: [] };
    }

    const parsed = JSON.parse(trimmed) as unknown;
    if (!Array.isArray(parsed)) {
      return { valid: false, errors: ['JSON root must be an array'], data: [] };
    }

    const data: Scenario[] = [];
    parsed.forEach((item, index) => {
      if (!isValidScenario(item)) {
        const missingFields = REQUIRED_JSON_FIELDS.filter((field) => {
          if (!isRecord(item)) {
            return true;
          }
          return !(field in item);
        });
        errors.push(
          `Invalid scenario at index ${index}${missingFields.length > 0 ? `: missing ${missingFields.join(', ')}` : ''}`,
        );
        return;
      }

      data.push(cloneScenario(item));
    });

    if (errors.length > 0) {
      return { valid: false, errors, data: [] };
    }

    return { valid: true, errors: [], data };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to parse JSON';
    return { valid: false, errors: [message], data: [] };
  }
}

export function parseCSVToScenarios(rows: string[][]): Scenario[] {
  try {
    if (rows.length <= 1) {
      return [];
    }

    const headerRow = rows[0].map(normalizeHeader);
    const columnIndex = (header: (typeof CSV_HEADERS)[number]): number =>
      headerRow.indexOf(normalizeHeader(header));

    const nameIndex = columnIndex('Scenario Name');
    const typeIndex = columnIndex('Type');
    const createdIndex = columnIndex('Date Created');
    const modifiedIndex = columnIndex('Last Modified');
    const inputsIndex = columnIndex('Inputs');
    const outputsIndex = columnIndex('Outputs');

    const now = new Date().toISOString();

    return rows.slice(1).flatMap((row) => {
      const name = row[nameIndex]?.trim();
      const calculatorType = row[typeIndex]?.trim();

      if (!name || !calculatorType) {
        return [];
      }

      const scenario: Scenario = {
        scenario_id: createScenarioId(),
        calculator_type: calculatorType,
        name,
        inputs: parseKeyValueString(row[inputsIndex] ?? ''),
        outputs: parseKeyValueString(row[outputsIndex] ?? ''),
        notes: '',
        created_at: now,
        last_modified: now,
      };

      const createdValue = row[createdIndex]?.trim();
      const modifiedValue = row[modifiedIndex]?.trim();
      if (createdValue) {
        const createdDate = new Date(createdValue);
        if (!Number.isNaN(createdDate.getTime())) {
          scenario.created_at = createdDate.toISOString();
        }
      }
      if (modifiedValue) {
        const modifiedDate = new Date(modifiedValue);
        if (!Number.isNaN(modifiedDate.getTime())) {
          scenario.last_modified = modifiedDate.toISOString();
        }
      }

      return [scenario];
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to parse CSV rows';
    throw new Error(message);
  }
}
