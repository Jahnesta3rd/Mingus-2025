import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import jsPDF from 'jspdf';
import {
  Building2,
  Calculator,
  ChevronRight,
  Copy,
  Download,
  Eye,
  FileText,
  Grid,
  LayoutList,
  Pencil,
  PiggyBank,
  Trash2,
  X,
} from 'lucide-react';
import {
  deleteScenario,
  duplicateScenario,
  getScenariosByType,
  loadScenarios,
  updateScenario,
  type Scenario,
} from '../utils/scenarioStorage';

type ViewMode = 'list' | 'grid';
type CalculatorType = 'retirement' | 'mortgage' | 'tax';
type FilterType = 'all' | CalculatorType;
type SortOption =
  | 'recent'
  | 'oldest'
  | 'alpha-asc'
  | 'alpha-desc'
  | 'by-type';
type ColumnSortKey = 'name' | 'calculator_type' | 'created_at' | 'last_modified';
type ModalMode = 'rename' | 'duplicate' | 'delete' | null;

interface FilterState {
  type: FilterType;
  dateFrom: string;
  dateTo: string;
  search: string;
}

interface ModalState {
  mode: ModalMode;
  scenarioId: string | null;
  name: string;
  notes: string;
}

const VIEW_MODE_KEY = 'scenario_view_mode';
const FILTER_STATE_KEY = 'scenario_filter_state';
const SORT_KEY = 'scenario_sort';

const TYPE_ORDER: CalculatorType[] = ['retirement', 'mortgage', 'tax'];

const TYPE_LABELS: Record<CalculatorType, string> = {
  retirement: 'Retirement',
  mortgage: 'Mortgage',
  tax: 'Tax',
};

const INPUT_LABELS: Record<string, string> = {
  currentAge: 'Current Age',
  retirementAge: 'Retirement Age',
  currentSavings: 'Current Savings',
  annualIncome: 'Annual Income',
  monthlySavings: 'Monthly Savings',
  homePrice: 'Home Price',
  downPayment: 'Down Payment',
  interestRate: 'Interest Rate',
  loanTermYears: 'Loan Term (Years)',
  grossIncome: 'Gross Income',
  deductions: 'Deductions',
};

const OUTPUT_LABELS: Record<string, string> = {
  yearsToRetirement: 'Years to Retirement',
  projectedSavings: 'Projected Savings',
  totalContributions: 'Total Contributions',
  monthlyPayment: 'Monthly Payment',
  totalPayment: 'Total Payment',
  totalInterest: 'Total Interest',
  taxableIncome: 'Taxable Income',
  estimatedTax: 'Estimated Tax',
  effectiveRate: 'Effective Rate',
};

const DEFAULT_FILTERS: FilterState = {
  type: 'all',
  dateFrom: '',
  dateTo: '',
  search: '',
};

function readLocalStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeLocalStorage(key: string, value: unknown): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(key, JSON.stringify(value));
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatFileName(value: string): string {
  return (
    value
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '') || 'scenario'
  );
}

function normalizeCalculatorType(value: string): CalculatorType | null {
  if (value === 'retirement' || value === 'mortgage' || value === 'tax') {
    return value;
  }
  return null;
}

function getTypeBadgeClass(type: string): string {
  switch (type) {
    case 'retirement':
      return 'bg-blue-100 text-blue-800';
    case 'mortgage':
      return 'bg-green-100 text-green-800';
    case 'tax':
      return 'bg-orange-100 text-orange-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

function formatFieldLabel(key: string, labels: Record<string, string>): string {
  return labels[key] ?? key.replace(/([A-Z])/g, ' $1').replace(/^./, (char) => char.toUpperCase());
}

function formatFieldValue(key: string, value: unknown): string {
  if (typeof value === 'number') {
    if (
      key.toLowerCase().includes('rate') ||
      key === 'effectiveRate' ||
      key === 'interestRate'
    ) {
      return `${value.toFixed(1)}%`;
    }
    if (
      key.toLowerCase().includes('age') ||
      key.toLowerCase().includes('years') ||
      key === 'yearsToRetirement' ||
      key === 'loanTermYears'
    ) {
      return String(value);
    }
    return formatCurrency(value);
  }
  return String(value ?? '—');
}

function exportScenarioPdf(scenario: Scenario): void {
  const pdf = new jsPDF();
  let y = 18;

  const addLine = (label: string, value: string) => {
    pdf.text(`${label}: ${value}`, 14, y);
    y += 8;
  };

  pdf.setFontSize(18);
  pdf.text('Scenario Export', 14, y);
  y += 12;

  pdf.setFontSize(11);
  addLine('Scenario name', scenario.name);
  addLine('Type', scenario.calculator_type);
  addLine('Date created', formatDate(scenario.created_at));
  addLine('Last modified', formatDate(scenario.last_modified));
  addLine('Notes', scenario.notes || 'None');
  y += 4;

  pdf.setFontSize(14);
  pdf.text('Inputs', 14, y);
  y += 8;
  pdf.setFontSize(11);

  Object.entries(scenario.inputs).forEach(([key, value]) => {
    addLine(formatFieldLabel(key, INPUT_LABELS), String(value));
  });

  y += 4;
  pdf.setFontSize(14);
  pdf.text('Outputs', 14, y);
  y += 8;
  pdf.setFontSize(11);

  Object.entries(scenario.outputs).forEach(([key, value]) => {
    addLine(formatFieldLabel(key, OUTPUT_LABELS), String(value));
  });

  pdf.save(`${formatFileName(scenario.name)}_${scenario.created_at.slice(0, 10)}.pdf`);
}

function sortScenarios(
  scenarios: Scenario[],
  sortOption: SortOption,
  columnSort: { key: ColumnSortKey; direction: 'asc' | 'desc' } | null,
): Scenario[] {
  const sorted = [...scenarios];

  if (columnSort) {
    const { key, direction } = columnSort;
    sorted.sort((left, right) => {
      const leftValue = left[key];
      const rightValue = right[key];
      const comparison =
        key === 'name' || key === 'calculator_type'
          ? leftValue.localeCompare(rightValue)
          : leftValue.localeCompare(rightValue);
      return direction === 'asc' ? comparison : -comparison;
    });
    return sorted;
  }

  switch (sortOption) {
    case 'oldest':
      sorted.sort((left, right) => left.last_modified.localeCompare(right.last_modified));
      break;
    case 'alpha-asc':
      sorted.sort((left, right) => left.name.localeCompare(right.name));
      break;
    case 'alpha-desc':
      sorted.sort((left, right) => right.name.localeCompare(left.name));
      break;
    case 'by-type':
      sorted.sort((left, right) => {
        const leftIndex = TYPE_ORDER.indexOf(left.calculator_type as CalculatorType);
        const rightIndex = TYPE_ORDER.indexOf(right.calculator_type as CalculatorType);
        const typeComparison =
          (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
        return typeComparison !== 0 ? typeComparison : left.name.localeCompare(right.name);
      });
      break;
    case 'recent':
    default:
      sorted.sort((left, right) => right.last_modified.localeCompare(left.last_modified));
      break;
  }

  return sorted;
}

function filterScenarios(scenarios: Scenario[], filters: FilterState): Scenario[] {
  return scenarios.filter((scenario) => {
    if (filters.type !== 'all' && scenario.calculator_type !== filters.type) {
      return false;
    }

    if (filters.search.trim()) {
      const query = filters.search.trim().toLowerCase();
      if (!scenario.name.toLowerCase().includes(query)) {
        return false;
      }
    }

    const createdDate = scenario.created_at.slice(0, 10);
    if (filters.dateFrom && createdDate < filters.dateFrom) {
      return false;
    }
    if (filters.dateTo && createdDate > filters.dateTo) {
      return false;
    }

    return true;
  });
}

interface ScenarioModalProps {
  modalState: ModalState;
  onClose: () => void;
  onChange: (nextState: ModalState) => void;
  onSubmit: () => void;
}

function ScenarioModal({
  modalState,
  onClose,
  onChange,
  onSubmit,
}: ScenarioModalProps): React.JSX.Element | null {
  if (!modalState.mode || modalState.mode === 'delete') return null;

  const title =
    modalState.mode === 'rename'
      ? 'Rename scenario'
      : 'Duplicate scenario - enter new name';

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 px-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
            <p className="mt-1 text-sm text-slate-500">
              Scenarios are stored locally in this browser only.
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

        <div className="space-y-4">
          <div>
            <label htmlFor="scenario-name" className="mb-2 block text-sm font-medium text-slate-700">
              Scenario name
            </label>
            <input
              id="scenario-name"
              type="text"
              value={modalState.name}
              onChange={(event) => onChange({ ...modalState, name: event.target.value })}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          {modalState.mode === 'duplicate' && (
            <div>
              <label
                htmlFor="scenario-notes"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Optional notes
              </label>
              <textarea
                id="scenario-notes"
                rows={4}
                value={modalState.notes}
                onChange={(event) => onChange({ ...modalState, notes: event.target.value })}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={!modalState.name.trim()}
            className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

interface DeleteModalProps {
  open: boolean;
  scenarioName: string;
  onClose: () => void;
  onConfirm: () => void;
}

function DeleteModal({
  open,
  scenarioName,
  onClose,
  onConfirm,
}: DeleteModalProps): React.JSX.Element | null {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Delete scenario</h2>
            <p className="mt-2 text-sm text-slate-600">
              Are you sure? This cannot be undone.
            </p>
            {scenarioName && (
              <p className="mt-2 text-sm font-medium text-slate-900">{scenarioName}</p>
            )}
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
            className="rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

interface DetailPanelProps {
  scenario: Scenario | null;
  onClose: () => void;
}

function DetailPanel({ scenario, onClose }: DetailPanelProps): React.JSX.Element | null {
  if (!scenario) return null;

  const calculatorType = normalizeCalculatorType(scenario.calculator_type);

  /*
  FY27: ADVISOR SHARING DEAD END

  Future feature stub for advisor integration:
  - "Share with Advisor" button on detail panel
  - Modal: Enter advisor email
  - Scenario becomes visible to advisor's dashboard
  - Advisor can build recommendation
  - Recommendation appears in client app

  For now: Disabled button showing "Coming FY27"
  Button: <button disabled>Share with Advisor (FY27)</button>
  */

  return (
    <>
      <button
        type="button"
        aria-label="Close detail panel overlay"
        className="fixed inset-0 z-40 bg-slate-900/30"
        onClick={onClose}
      />
      <aside className="fixed right-0 top-0 z-50 flex h-full w-full max-w-sm flex-col bg-white shadow-lg sm:w-96">
        <div className="flex items-start justify-between border-b border-gray-200 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{scenario.name}</h2>
            <span
              className={`mt-2 inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${getTypeBadgeClass(scenario.calculator_type)}`}
            >
              {calculatorType ? TYPE_LABELS[calculatorType] : scenario.calculator_type}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
            aria-label="Close detail panel"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <section className="mb-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Inputs
            </h3>
            <dl className="space-y-2">
              {Object.entries(scenario.inputs).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-start justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2"
                >
                  <dt className="text-sm text-slate-600">{formatFieldLabel(key, INPUT_LABELS)}</dt>
                  <dd className="text-sm font-medium text-slate-900">
                    {formatFieldValue(key, value)}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="mb-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Outputs
            </h3>
            <dl className="space-y-2">
              {Object.entries(scenario.outputs).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-start justify-between gap-3 rounded-lg bg-blue-50 px-3 py-2"
                >
                  <dt className="text-sm text-slate-600">{formatFieldLabel(key, OUTPUT_LABELS)}</dt>
                  <dd className="text-sm font-medium text-slate-900">
                    {formatFieldValue(key, value)}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          {scenario.notes && (
            <section className="mb-6">
              <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Notes
              </h3>
              <p className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-slate-700">
                {scenario.notes}
              </p>
            </section>
          )}

          <section className="space-y-2 text-sm text-slate-600">
            <p>
              <span className="font-medium text-slate-700">Created:</span>{' '}
              {formatDateTime(scenario.created_at)}
            </p>
            <p>
              <span className="font-medium text-slate-700">Last modified:</span>{' '}
              {formatDateTime(scenario.last_modified)}
            </p>
          </section>

          <div className="mt-6">
            <button
              type="button"
              disabled
              className="w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-medium text-slate-400"
            >
              Share with Advisor (FY27)
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

function ActionButtons({
  scenario,
  onView,
  onDuplicate,
  onRename,
  onDelete,
  onExport,
  compact = false,
}: {
  scenario: Scenario;
  onView: (scenario: Scenario) => void;
  onDuplicate: (scenario: Scenario) => void;
  onRename: (scenario: Scenario) => void;
  onDelete: (scenario: Scenario) => void;
  onExport: (scenario: Scenario) => void;
  compact?: boolean;
}): React.JSX.Element {
  const buttonClass = compact
    ? 'rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50'
    : 'rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50';

  return (
    <div className="flex flex-wrap gap-1.5">
      <button type="button" onClick={() => onView(scenario)} className={`${buttonClass} bg-blue-600 text-white hover:bg-blue-700`}>
        <Eye className="mr-1 inline h-3.5 w-3.5" />
        View
      </button>
      <button type="button" onClick={() => onDuplicate(scenario)} className={buttonClass}>
        <Copy className="mr-1 inline h-3.5 w-3.5" />
        Duplicate
      </button>
      <button type="button" onClick={() => onRename(scenario)} className={buttonClass}>
        <Pencil className="mr-1 inline h-3.5 w-3.5" />
        Rename
      </button>
      <button
        type="button"
        onClick={() => onDelete(scenario)}
        className={`${buttonClass} border-red-200 text-red-700 hover:bg-red-50`}
      >
        <Trash2 className="mr-1 inline h-3.5 w-3.5" />
        Delete
      </button>
      <button type="button" onClick={() => onExport(scenario)} className={buttonClass}>
        <Download className="mr-1 inline h-3.5 w-3.5" />
        Export
      </button>
    </div>
  );
}

const ScenarioManagement: React.FC = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const stored = readLocalStorage<string>(VIEW_MODE_KEY, 'list');
    return stored === 'grid' ? 'grid' : 'list';
  });
  const [filters, setFilters] = useState<FilterState>(() =>
    readLocalStorage(FILTER_STATE_KEY, DEFAULT_FILTERS),
  );
  const [sortOption, setSortOption] = useState<SortOption>(() =>
    readLocalStorage<SortOption>(SORT_KEY, 'recent'),
  );
  const [columnSort, setColumnSort] = useState<{
    key: ColumnSortKey;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailScenario, setDetailScenario] = useState<Scenario | null>(null);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [modalState, setModalState] = useState<ModalState>({
    mode: null,
    scenarioId: null,
    name: '',
    notes: '',
  });
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [message, setMessage] = useState('');

  const refreshScenarios = useCallback(() => {
    setScenarios(loadScenarios());
  }, []);

  useEffect(() => {
    refreshScenarios();
  }, [refreshScenarios]);

  useEffect(() => {
    writeLocalStorage(VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  useEffect(() => {
    writeLocalStorage(FILTER_STATE_KEY, filters);
  }, [filters]);

  useEffect(() => {
    writeLocalStorage(SORT_KEY, sortOption);
  }, [sortOption]);

  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(() => setMessage(''), 3500);
    return () => window.clearTimeout(timer);
  }, [message]);

  const stats = useMemo(
    () => ({
      total: scenarios.length,
      retirement: getScenariosByType('retirement').length,
      mortgage: getScenariosByType('mortgage').length,
      tax: getScenariosByType('tax').length,
    }),
    [scenarios],
  );

  const filteredScenarios = useMemo(
    () => sortScenarios(filterScenarios(scenarios, filters), sortOption, columnSort),
    [scenarios, filters, sortOption, columnSort],
  );

  const filtersActive =
    filters.type !== 'all' ||
    filters.search.trim() !== '' ||
    filters.dateFrom !== '' ||
    filters.dateTo !== '';

  const allVisibleSelected =
    filteredScenarios.length > 0 &&
    filteredScenarios.every((scenario) => selectedIds.has(scenario.scenario_id));

  const handleColumnSort = (key: ColumnSortKey) => {
    setSortOption('recent');
    setColumnSort((previous) => {
      if (previous?.key === key) {
        return { key, direction: previous.direction === 'asc' ? 'desc' : 'asc' };
      }
      const defaultDirection = key === 'last_modified' || key === 'created_at' ? 'desc' : 'asc';
      return { key, direction: defaultDirection };
    });
  };

  const handleSortDropdown = (value: SortOption) => {
    setSortOption(value);
    setColumnSort(null);
  };

  const clearFilters = () => {
    setFilters(DEFAULT_FILTERS);
  };

  const toggleSelectAll = () => {
    if (allVisibleSelected) {
      setSelectedIds(new Set());
      return;
    }
    setSelectedIds(new Set(filteredScenarios.map((scenario) => scenario.scenario_id)));
  };

  const toggleSelect = (scenarioId: string) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (next.has(scenarioId)) {
        next.delete(scenarioId);
      } else {
        next.add(scenarioId);
      }
      return next;
    });
  };

  const closeModal = () => {
    setModalState({ mode: null, scenarioId: null, name: '', notes: '' });
  };

  const handleModalSubmit = () => {
    if (!modalState.mode || !modalState.scenarioId || !modalState.name.trim()) return;

    if (modalState.mode === 'rename') {
      const updated = updateScenario(modalState.scenarioId, {
        name: modalState.name,
      });
      if (updated) {
        refreshScenarios();
        if (detailScenario?.scenario_id === updated.scenario_id) {
          setDetailScenario(updated);
        }
        setMessage(`Scenario renamed: ${updated.name}`);
      }
      closeModal();
      return;
    }

    const duplicated = duplicateScenario(modalState.scenarioId, modalState.name);
    if (duplicated) {
      if (modalState.notes.trim()) {
        updateScenario(duplicated.scenario_id, { notes: modalState.notes });
      }
      refreshScenarios();
      setMessage(`Scenario duplicated: ${duplicated.name}`);
    }
    closeModal();
  };

  const handleDeleteConfirm = () => {
    if (bulkDeleteOpen) {
      selectedIds.forEach((id) => deleteScenario(id));
      setSelectedIds(new Set());
      if (detailScenario && selectedIds.has(detailScenario.scenario_id)) {
        setDetailScenario(null);
      }
      refreshScenarios();
      setMessage('Selected scenarios deleted.');
      setBulkDeleteOpen(false);
      return;
    }

    if (!deleteTarget) return;
    deleteScenario(deleteTarget.id);
    if (detailScenario?.scenario_id === deleteTarget.id) {
      setDetailScenario(null);
    }
    setSelectedIds((previous) => {
      const next = new Set(previous);
      next.delete(deleteTarget.id);
      return next;
    });
    refreshScenarios();
    setMessage('Scenario deleted.');
    setDeleteTarget(null);
  };

  const handleBulkExport = () => {
    scenarios
      .filter((scenario) => selectedIds.has(scenario.scenario_id))
      .forEach((scenario) => exportScenarioPdf(scenario));
    setMessage(`Exported ${selectedIds.size} scenario(s).`);
  };

  const renderSortIndicator = (key: ColumnSortKey) => {
    if (columnSort?.key !== key) return null;
    return columnSort.direction === 'asc' ? ' ↑' : ' ↓';
  };

  const sidebarContent = (
    <div className="space-y-5">
      <div>
        <label htmlFor="filter-type" className="mb-2 block text-sm font-medium text-slate-700">
          Filter by Type
        </label>
        <select
          id="filter-type"
          value={filters.type}
          onChange={(event) =>
            setFilters((previous) => ({
              ...previous,
              type: event.target.value as FilterType,
            }))
          }
          className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        >
          <option value="all">All</option>
          <option value="retirement">Retirement</option>
          <option value="mortgage">Mortgage</option>
          <option value="tax">Tax</option>
        </select>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-slate-700">Date Range</p>
        <div className="space-y-2">
          <div>
            <label htmlFor="date-from" className="mb-1 block text-xs text-slate-500">
              From
            </label>
            <input
              id="date-from"
              type="date"
              value={filters.dateFrom}
              onChange={(event) =>
                setFilters((previous) => ({ ...previous, dateFrom: event.target.value }))
              }
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <div>
            <label htmlFor="date-to" className="mb-1 block text-xs text-slate-500">
              To
            </label>
            <input
              id="date-to"
              type="date"
              value={filters.dateTo}
              onChange={(event) =>
                setFilters((previous) => ({ ...previous, dateTo: event.target.value }))
              }
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>
      </div>

      <div>
        <label htmlFor="search-scenarios" className="mb-2 block text-sm font-medium text-slate-700">
          Search
        </label>
        <input
          id="search-scenarios"
          type="text"
          placeholder="Search by scenario name"
          value={filters.search}
          onChange={(event) =>
            setFilters((previous) => ({ ...previous, search: event.target.value }))
          }
          className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      <div>
        <label htmlFor="sort-by" className="mb-2 block text-sm font-medium text-slate-700">
          Sort by
        </label>
        <select
          id="sort-by"
          value={sortOption}
          onChange={(event) => handleSortDropdown(event.target.value as SortOption)}
          className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        >
          <option value="recent">Most Recently Modified</option>
          <option value="oldest">Oldest</option>
          <option value="alpha-asc">Alphabetical (A-Z)</option>
          <option value="alpha-desc">Alphabetical (Z-A)</option>
          <option value="by-type">By Type (Retirement → Mortgage → Tax)</option>
        </select>
      </div>

      {filtersActive && (
        <button
          type="button"
          onClick={clearFilters}
          className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Clear Filters
        </button>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6">
          <nav className="mb-2 flex items-center gap-1 text-sm text-slate-500">
            <Link to="/" className="hover:text-blue-600">
              Home
            </Link>
            <ChevronRight className="h-4 w-4" />
            <Link to="/enhanced-calculator" className="hover:text-blue-600">
              Calculators
            </Link>
            <ChevronRight className="h-4 w-4" />
            <span className="font-medium text-slate-900">Scenario Management</span>
          </nav>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="text-3xl font-semibold text-slate-900">Scenario Management</h1>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setViewMode('list')}
                className={`inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <LayoutList className="mr-2 h-4 w-4" />
                List View
              </button>
              <button
                type="button"
                onClick={() => setViewMode('grid')}
                className={`inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Grid className="mr-2 h-4 w-4" />
                Grid View
              </button>
            </div>
          </div>
        </header>

        {message && (
          <div className="mb-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm font-medium text-green-800">
            {message}
          </div>
        )}

        <section className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-slate-100 p-3 text-slate-700">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Scenarios</p>
                <p className="text-2xl font-semibold text-slate-900">{stats.total}</p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-blue-50 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-100 p-3 text-blue-700">
                <PiggyBank className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-blue-700">Retirement Plans</p>
                <p className="text-2xl font-semibold text-blue-900">{stats.retirement}</p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-green-50 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-green-100 p-3 text-green-700">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-green-700">Mortgage Plans</p>
                <p className="text-2xl font-semibold text-green-900">{stats.mortgage}</p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-orange-50 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-orange-100 p-3 text-orange-700">
                <Calculator className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-orange-700">Tax Plans</p>
                <p className="text-2xl font-semibold text-orange-900">{stats.tax}</p>
              </div>
            </div>
          </div>
        </section>

        {selectedIds.size > 0 && (
          <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3">
            <span className="text-sm font-medium text-blue-900">
              {selectedIds.size} selected
            </span>
            <button
              type="button"
              onClick={() => setBulkDeleteOpen(true)}
              className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
            >
              Delete Selected
            </button>
            <button
              type="button"
              onClick={handleBulkExport}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Export Selected
            </button>
          </div>
        )}

        <div className="flex flex-col gap-6 lg:flex-row">
          <aside className="hidden w-full shrink-0 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm lg:block lg:w-72">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Filters
            </h2>
            {sidebarContent}
          </aside>

          <div className="min-w-0 flex-1">
            <div className="mb-4 lg:hidden">
              <button
                type="button"
                onClick={() => setMobileFiltersOpen((previous) => !previous)}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm"
              >
                {mobileFiltersOpen ? 'Hide Filters' : 'Show Filters & Sort'}
              </button>
              {mobileFiltersOpen && (
                <div className="mt-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                  {sidebarContent}
                </div>
              )}
            </div>

            <main className="rounded-2xl border border-gray-200 bg-white shadow-sm">
              {filteredScenarios.length === 0 ? (
                <div className="px-6 py-16 text-center text-sm text-slate-500">
                  No scenarios saved yet. Go to calculators to create one.
                </div>
              ) : viewMode === 'list' ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <th className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={allVisibleSelected}
                            onChange={toggleSelectAll}
                            aria-label="Select all scenarios"
                          />
                        </th>
                        <th className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => handleColumnSort('name')}
                            className="hover:text-slate-900"
                          >
                            Scenario Name{renderSortIndicator('name')}
                          </button>
                        </th>
                        <th className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => handleColumnSort('calculator_type')}
                            className="hover:text-slate-900"
                          >
                            Calculator Type{renderSortIndicator('calculator_type')}
                          </button>
                        </th>
                        <th className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => handleColumnSort('created_at')}
                            className="hover:text-slate-900"
                          >
                            Date Created{renderSortIndicator('created_at')}
                          </button>
                        </th>
                        <th className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => handleColumnSort('last_modified')}
                            className="hover:text-slate-900"
                          >
                            Last Modified{renderSortIndicator('last_modified')}
                          </button>
                        </th>
                        <th className="px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredScenarios.map((scenario) => {
                        const calculatorType = normalizeCalculatorType(scenario.calculator_type);
                        return (
                          <tr
                            key={scenario.scenario_id}
                            className="border-b border-gray-200 hover:bg-gray-50"
                          >
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                checked={selectedIds.has(scenario.scenario_id)}
                                onChange={() => toggleSelect(scenario.scenario_id)}
                                aria-label={`Select ${scenario.name}`}
                              />
                            </td>
                            <td className="px-4 py-3 font-medium text-slate-900">
                              {scenario.name}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${getTypeBadgeClass(scenario.calculator_type)}`}
                              >
                                {calculatorType
                                  ? TYPE_LABELS[calculatorType]
                                  : scenario.calculator_type}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-slate-600">
                              {formatDate(scenario.created_at)}
                            </td>
                            <td className="px-4 py-3 text-slate-600">
                              {formatDate(scenario.last_modified)}
                            </td>
                            <td className="px-4 py-3">
                              <ActionButtons
                                scenario={scenario}
                                onView={setDetailScenario}
                                onDuplicate={(item) =>
                                  setModalState({
                                    mode: 'duplicate',
                                    scenarioId: item.scenario_id,
                                    name: `${item.name} - Copy`,
                                    notes: item.notes,
                                  })
                                }
                                onRename={(item) =>
                                  setModalState({
                                    mode: 'rename',
                                    scenarioId: item.scenario_id,
                                    name: item.name,
                                    notes: item.notes,
                                  })
                                }
                                onDelete={(item) =>
                                  setDeleteTarget({
                                    id: item.scenario_id,
                                    name: item.name,
                                  })
                                }
                                onExport={(item) => exportScenarioPdf(item)}
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 xl:grid-cols-3">
                  {filteredScenarios.map((scenario) => {
                    const calculatorType = normalizeCalculatorType(scenario.calculator_type);
                    return (
                      <article
                        key={scenario.scenario_id}
                        role="button"
                        tabIndex={0}
                        onClick={() => setDetailScenario(scenario)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setDetailScenario(scenario);
                          }
                        }}
                        className="flex cursor-pointer flex-col rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md"
                      >
                        <h3 className="text-base font-semibold text-slate-900">{scenario.name}</h3>
                        <span
                          className={`mt-2 inline-flex w-fit rounded-full px-2.5 py-0.5 text-xs font-semibold ${getTypeBadgeClass(scenario.calculator_type)}`}
                        >
                          {calculatorType ? TYPE_LABELS[calculatorType] : scenario.calculator_type}
                        </span>
                        <div className="mt-3 space-y-1 text-xs text-slate-500">
                          <p>Created: {formatDate(scenario.created_at)}</p>
                          <p>Modified: {formatDate(scenario.last_modified)}</p>
                        </div>
                        <div
                          className="mt-4 border-t border-gray-100 pt-3"
                          onClick={(event) => event.stopPropagation()}
                          onKeyDown={(event) => event.stopPropagation()}
                        >
                          <ActionButtons
                            compact
                            scenario={scenario}
                            onView={setDetailScenario}
                            onDuplicate={(item) =>
                              setModalState({
                                mode: 'duplicate',
                                scenarioId: item.scenario_id,
                                name: `${item.name} - Copy`,
                                notes: item.notes,
                              })
                            }
                            onRename={(item) =>
                              setModalState({
                                mode: 'rename',
                                scenarioId: item.scenario_id,
                                name: item.name,
                                notes: item.notes,
                              })
                            }
                            onDelete={(item) =>
                              setDeleteTarget({
                                id: item.scenario_id,
                                name: item.name,
                              })
                            }
                            onExport={(item) => exportScenarioPdf(item)}
                          />
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </main>
          </div>
        </div>
      </div>

      <DetailPanel scenario={detailScenario} onClose={() => setDetailScenario(null)} />

      <ScenarioModal
        modalState={modalState}
        onClose={closeModal}
        onChange={setModalState}
        onSubmit={handleModalSubmit}
      />

      <DeleteModal
        open={Boolean(deleteTarget) || bulkDeleteOpen}
        scenarioName={
          bulkDeleteOpen ? `${selectedIds.size} selected scenario(s)` : deleteTarget?.name ?? ''
        }
        onClose={() => {
          setDeleteTarget(null);
          setBulkDeleteOpen(false);
        }}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
};

export default ScenarioManagement;
