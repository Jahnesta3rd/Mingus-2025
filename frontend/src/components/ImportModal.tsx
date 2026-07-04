import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { X } from 'lucide-react';
import {
  deleteBackup,
  listBackups,
  parseCSVToScenarios,
  restoreBackup,
  validateCSVStructure,
  validateJSONStructure,
} from '../utils/exportUtils';
import { saveScenario, type Scenario } from '../utils/scenarioStorage';

type ImportTab = 'backup' | 'csv' | 'json';

type ConfirmModalState =
  | {
      type: 'restore';
      backupKey: string;
      count: number;
      dateLabel: string;
    }
  | {
      type: 'delete';
      backupKey: string;
    }
  | null;

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: (count: number) => void;
}

interface BackupEntry {
  timestamp: string;
  count: number;
  key: string;
}

interface CSVValidationState {
  valid: boolean;
  errors: string[];
  rows: string[][];
}

interface JSONValidationState {
  valid: boolean;
  errors: string[];
  data: Scenario[];
}

const PREVIEW_COLUMNS = [
  'Scenario Name',
  'Type',
  'Date Created',
  'Inputs',
  'Outputs',
] as const;

function formatBackupTimestamp(timestamp: string): string {
  const [datePart, timePart] = timestamp.split('_');
  if (!datePart || !timePart) {
    return timestamp;
  }

  const [year, month, day] = datePart.split('-').map(Number);
  const [hour, minute] = timePart.split('-').map(Number);
  const date = new Date(year, month - 1, day, hour, minute);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  const dateLabel = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const timeLabel = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });

  return `${dateLabel} at ${timeLabel}`;
}

function getColumnIndex(headerRow: string[], columnName: string): number {
  const normalized = columnName.trim().toLowerCase();
  return headerRow.findIndex((header) => header.trim().toLowerCase() === normalized);
}

function saveImportedScenarios(scenarios: Scenario[]): number {
  let savedCount = 0;

  scenarios.forEach((scenario) => {
    saveScenario({
      scenario_id: scenario.scenario_id,
      calculator_type: scenario.calculator_type,
      name: scenario.name,
      inputs: scenario.inputs,
      outputs: scenario.outputs,
      notes: scenario.notes,
      created_at: scenario.created_at,
    });
    savedCount += 1;
  });

  return savedCount;
}

interface ConfirmModalProps {
  title: string;
  message: string;
  confirmLabel: string;
  confirmClassName?: string;
  onClose: () => void;
  onConfirm: () => void;
}

function ConfirmModal({
  title,
  message,
  confirmLabel,
  confirmClassName = 'bg-blue-600 hover:bg-blue-700',
  onClose,
  onConfirm,
}: ConfirmModalProps): React.JSX.Element {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
            <p className="mt-2 text-sm text-slate-600">{message}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold text-white ${confirmClassName}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function ImportModal({ isOpen, onClose, onImportComplete }: ImportModalProps): React.JSX.Element | null {
  const [activeTab, setActiveTab] = useState<ImportTab>('backup');
  const [backups, setBackups] = useState<BackupEntry[]>([]);
  const [confirmModal, setConfirmModal] = useState<ConfirmModalState>(null);
  const [statusMessage, setStatusMessage] = useState('');

  const [csvFileName, setCsvFileName] = useState('');
  const [csvValidation, setCsvValidation] = useState<CSVValidationState>({
    valid: false,
    errors: [],
    rows: [],
  });

  const [jsonText, setJsonText] = useState('');
  const [jsonValidation, setJsonValidation] = useState<JSONValidationState>({
    valid: false,
    errors: [],
    data: [],
  });

  const refreshBackups = useCallback(() => {
    setBackups(listBackups());
  }, []);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    refreshBackups();
    setActiveTab('backup');
    setConfirmModal(null);
    setStatusMessage('');
    setCsvFileName('');
    setCsvValidation({ valid: false, errors: [], rows: [] });
    setJsonText('');
    setJsonValidation({ valid: false, errors: [], data: [] });
  }, [isOpen, refreshBackups]);

  const csvScenarioCount = useMemo(() => {
    if (!csvValidation.valid || csvValidation.rows.length <= 1) {
      return 0;
    }
    return csvValidation.rows.length - 1;
  }, [csvValidation]);

  const csvPreviewRows = useMemo(() => {
    if (csvValidation.rows.length === 0) {
      return [];
    }

    return csvValidation.rows.slice(0, 3);
  }, [csvValidation.rows]);

  const csvPreviewColumnIndexes = useMemo(() => {
    if (csvValidation.rows.length === 0) {
      return PREVIEW_COLUMNS.map(() => -1);
    }

    const headerRow = csvValidation.rows[0];
    return PREVIEW_COLUMNS.map((column) => getColumnIndex(headerRow, column));
  }, [csvValidation.rows]);

  const handleCsvFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setCsvFileName(file.name);
    setStatusMessage('');

    try {
      const text = await file.text();
      const validation = validateCSVStructure(text);
      setCsvValidation(validation);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to read CSV file';
      setCsvValidation({ valid: false, errors: [message], rows: [] });
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonText(value);
    setStatusMessage('');

    if (!value.trim()) {
      setJsonValidation({ valid: false, errors: [], data: [] });
      return;
    }

    setJsonValidation(validateJSONStructure(value));
  };

  const completeImport = (count: number, message: string) => {
    setStatusMessage(message);
    onImportComplete(count);
    onClose();
  };

  const handleRestoreConfirm = () => {
    if (!confirmModal || confirmModal.type !== 'restore') {
      return;
    }

    const result = restoreBackup(confirmModal.backupKey);
    setConfirmModal(null);

    if (!result.success && result.errors.length > 0) {
      setStatusMessage(`✗ Restore failed: ${result.errors.join(', ')}`);
      return;
    }

    refreshBackups();
    completeImport(result.restored, `✓ Restored ${result.restored} scenarios`);
  };

  const handleDeleteConfirm = () => {
    if (!confirmModal || confirmModal.type !== 'delete') {
      return;
    }

    deleteBackup(confirmModal.backupKey);
    setConfirmModal(null);
    refreshBackups();
  };

  const handleCsvImport = () => {
    if (!csvValidation.valid) {
      return;
    }

    try {
      const scenarios = parseCSVToScenarios(csvValidation.rows);
      const count = saveImportedScenarios(scenarios);
      completeImport(count, `✓ Imported ${count} scenarios`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import CSV';
      setStatusMessage(`✗ Import failed: ${message}`);
    }
  };

  const handleJsonImport = () => {
    if (!jsonValidation.valid) {
      return;
    }

    try {
      const count = saveImportedScenarios(jsonValidation.data);
      completeImport(count, `✓ Imported ${count} scenarios`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import JSON';
      setStatusMessage(`✗ Import failed: ${message}`);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
        <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-lg">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Import Scenarios</h2>
              <p className="mt-1 text-sm text-slate-500">
                Restore from backup or import CSV/JSON
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
              aria-label="Close modal"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mb-6 flex gap-2 border-b border-slate-200">
            {([
              ['backup', 'Backup Restore'],
              ['csv', 'CSV Import'],
              ['json', 'JSON Import'],
            ] as const).map(([tab, label]) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {statusMessage && (
            <p
              className={`mb-4 text-sm ${
                statusMessage.startsWith('✓') ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {statusMessage}
            </p>
          )}

          {activeTab === 'backup' && (
            <div className="space-y-4">
              {backups.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No backups available yet. Use bulk export to create one.
                </p>
              ) : (
                <ul className="space-y-3">
                  {backups.map((backup) => (
                    <li
                      key={backup.key}
                      className="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {formatBackupTimestamp(backup.timestamp)}
                        </p>
                        <p className="mt-1 text-sm text-slate-500">
                          {backup.count} {backup.count === 1 ? 'scenario' : 'scenarios'}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setConfirmModal({
                              type: 'restore',
                              backupKey: backup.key,
                              count: backup.count,
                              dateLabel: formatBackupTimestamp(backup.timestamp),
                            })
                          }
                          className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                        >
                          Restore
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            setConfirmModal({
                              type: 'delete',
                              backupKey: backup.key,
                            })
                          }
                          className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Delete
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {activeTab === 'csv' && (
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="csv-file-input"
                  className="inline-flex cursor-pointer items-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                >
                  Choose CSV file
                </label>
                <input
                  id="csv-file-input"
                  type="file"
                  accept=".csv"
                  onChange={handleCsvFileChange}
                  className="hidden"
                />
                {csvFileName && (
                  <p className="mt-2 text-sm text-slate-600">{csvFileName}</p>
                )}
              </div>

              {csvPreviewRows.length > 0 && (
                <div className="max-h-48 overflow-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-100 text-slate-700">
                      <tr>
                        {PREVIEW_COLUMNS.map((column) => (
                          <th key={column} className="px-3 py-2 font-medium">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {csvPreviewRows.slice(1).map((row, rowIndex) => (
                        <tr
                          key={`preview-row-${rowIndex}`}
                          className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-slate-50'}
                        >
                          {csvPreviewColumnIndexes.map((columnIndex, cellIndex) => (
                            <td key={`${rowIndex}-${cellIndex}`} className="px-3 py-2 text-slate-700">
                              {columnIndex >= 0 ? row[columnIndex] ?? '' : ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {csvFileName && (
                <p
                  className={`text-sm ${
                    csvValidation.valid ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {csvValidation.valid
                    ? `✓ Valid CSV format (${csvScenarioCount} scenarios)`
                    : `✗ Invalid CSV: ${csvValidation.errors.join(', ') || 'Unknown error'}`}
                </p>
              )}

              <button
                type="button"
                onClick={handleCsvImport}
                disabled={!csvValidation.valid}
                className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Import
              </button>
            </div>
          )}

          {activeTab === 'json' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="json-import-text" className="mb-2 block text-sm font-medium text-slate-700">
                  Paste JSON here
                </label>
                <textarea
                  id="json-import-text"
                  rows={8}
                  value={jsonText}
                  onChange={(event) => handleJsonChange(event.target.value)}
                  placeholder='[{"scenario_id": "...", "name": "...", ...}, ...]'
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 font-mono text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              {jsonText.trim() && (
                <p
                  className={`text-sm ${
                    jsonValidation.valid ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {jsonValidation.valid
                    ? `✓ Valid JSON (${jsonValidation.data.length} scenarios)`
                    : `✗ Invalid JSON: ${jsonValidation.errors.join(', ') || 'Unknown error'}`}
                </p>
              )}

              <button
                type="button"
                onClick={handleJsonImport}
                disabled={!jsonValidation.valid}
                className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Import
              </button>
            </div>
          )}
        </div>
      </div>

      {confirmModal?.type === 'restore' && (
        <ConfirmModal
          title="Restore backup"
          message={`Restore ${confirmModal.count} scenarios from ${confirmModal.dateLabel}? This will replace current scenarios.`}
          confirmLabel="Restore"
          onClose={() => setConfirmModal(null)}
          onConfirm={handleRestoreConfirm}
        />
      )}

      {confirmModal?.type === 'delete' && (
        <ConfirmModal
          title="Delete backup"
          message="Delete this backup? This cannot be undone."
          confirmLabel="Delete"
          confirmClassName="bg-red-600 hover:bg-red-700"
          onClose={() => setConfirmModal(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}
    </>
  );
}

export default ImportModal;
