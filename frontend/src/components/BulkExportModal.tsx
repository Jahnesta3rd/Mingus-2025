import React, { useEffect, useState } from 'react';
import { Archive, FileJson, Loader2, Shield, Table, X } from 'lucide-react';
import {
  createBackup,
  downloadCSV,
  downloadJSON,
  exportScenariosAsCSV,
  exportScenariosAsJSON,
  exportScenariosAsZip,
  getTodayDateString,
} from '../utils/exportUtils';
import type { Scenario } from '../utils/scenarioStorage';

interface BulkExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarios: Scenario[];
  onImportClick?: () => void;
}

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

function BulkExportModal({
  isOpen,
  onClose,
  scenarios,
  onImportClick,
}: BulkExportModalProps): React.JSX.Element | null {
  const [toast, setToast] = useState('');
  const [toastIsError, setToastIsError] = useState(false);
  const [isZipLoading, setIsZipLoading] = useState(false);
  const [isBackupDisabled, setIsBackupDisabled] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setToast('');
    setToastIsError(false);
    setIsZipLoading(false);
    setIsBackupDisabled(false);
  }, [isOpen]);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timer = window.setTimeout(() => setToast(''), 3500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const showToast = (message: string, isError = false) => {
    setToast(message);
    setToastIsError(isError);
  };

  const exportFilename = (extension: 'csv' | 'json' | 'zip'): string =>
    `scenarios_${getTodayDateString()}.${extension}`;

  const handleCsvExport = () => {
    try {
      const csvContent = exportScenariosAsCSV(scenarios);
      downloadCSV(csvContent, exportFilename('csv'));
      showToast(`✓ CSV exported (${scenarios.length} scenarios)`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'CSV export failed';
      showToast(`✗ ${message}`, true);
    }
  };

  const handleZipExport = async () => {
    setIsZipLoading(true);

    try {
      await exportScenariosAsZip(scenarios);
      showToast(`✓ ZIP exported (${scenarios.length} scenarios, ${scenarios.length} PDFs)`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'ZIP export failed';
      showToast(`✗ ${message}`, true);
    } finally {
      setIsZipLoading(false);
    }
  };

  const handleJsonExport = () => {
    try {
      const jsonContent = exportScenariosAsJSON(scenarios);
      downloadJSON(jsonContent, exportFilename('json'));
      showToast(`✓ JSON exported (${scenarios.length} scenarios)`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'JSON export failed';
      showToast(`✗ ${message}`, true);
    }
  };

  const handleCreateBackup = () => {
    setIsBackupDisabled(true);

    try {
      const result = createBackup();

      if (!result.success) {
        showToast('✗ Backup failed', true);
        return;
      }

      showToast(
        `✓ Backup created: ${formatBackupTimestamp(result.timestamp)} (${result.count} scenarios)`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Backup failed';
      showToast(`✗ ${message}`, true);
    } finally {
      window.setTimeout(() => setIsBackupDisabled(false), 1500);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-lg">
        {isZipLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-white/80">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" aria-label="Generating ZIP" />
          </div>
        )}

        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Export Scenarios</h2>
            <p className="mt-1 text-sm text-slate-500">Choose export format</p>
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

        {toast && (
          <div
            className={`mb-4 rounded-xl border px-4 py-3 text-sm font-medium ${
              toastIsError
                ? 'border-red-200 bg-red-50 text-red-800'
                : 'border-green-200 bg-green-50 text-green-800'
            }`}
          >
            {toast}
          </div>
        )}

        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 p-4 transition hover:bg-gray-50 hover:shadow-md">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                <Table className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-slate-900">CSV</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Export all scenarios as a CSV spreadsheet. Open in Excel or Google Sheets.
                </p>
                <button
                  type="button"
                  onClick={handleCsvExport}
                  disabled={isZipLoading}
                  className="mt-3 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Export as CSV
                </button>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 p-4 transition hover:bg-gray-50 hover:shadow-md">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                <Archive className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-slate-900">ZIP</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Export all scenarios as PDFs in a ZIP file. One PDF per scenario.
                </p>
                <button
                  type="button"
                  onClick={handleZipExport}
                  disabled={isZipLoading}
                  className="mt-3 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Export as ZIP
                </button>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 p-4 transition hover:bg-gray-50 hover:shadow-md">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                <FileJson className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-slate-900">JSON</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Export all scenarios as JSON. For backup or integration with other tools.
                </p>
                <button
                  type="button"
                  onClick={handleJsonExport}
                  disabled={isZipLoading}
                  className="mt-3 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Export as JSON
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-slate-200 p-4">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-green-50 p-3 text-green-600">
              <Shield className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-slate-900">Create Backup</h3>
              <p className="mt-1 text-sm text-slate-600">
                Automatically save backup to localStorage for quick restore
              </p>
              <button
                type="button"
                onClick={handleCreateBackup}
                disabled={isBackupDisabled || isZipLoading}
                className="mt-3 rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Create Backup Now
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-slate-200 pt-4">
          {onImportClick ? (
            <button
              type="button"
              onClick={onImportClick}
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              Need to import?
            </button>
          ) : (
            <span />
          )}
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default BulkExportModal;
