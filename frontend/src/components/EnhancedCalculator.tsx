import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import jsPDF from 'jspdf';
import {
  Calculator,
  Copy,
  Download,
  FolderOpen,
  Pencil,
  Save,
  Trash2,
  X,
} from 'lucide-react';
import {
  deleteScenario,
  duplicateScenario,
  loadScenarios,
  saveScenario,
  updateScenario,
  type Scenario,
} from '../utils/scenarioStorage';

type CalculatorType = 'retirement' | 'mortgage' | 'tax';
type ViewMode = 'calculator' | 'scenarios';
type ModalMode = 'save' | 'rename' | 'duplicate' | null;

interface RetirementInputs {
  currentAge: number;
  retirementAge: number;
  currentSavings: number;
  annualIncome: number;
  monthlySavings: number;
}

interface MortgageInputs {
  homePrice: number;
  downPayment: number;
  interestRate: number;
  loanTermYears: number;
}

interface TaxInputs {
  grossIncome: number;
  deductions: number;
}

interface RetirementResults {
  yearsToRetirement: number;
  projectedSavings: number;
  annualIncome: number;
  totalContributions: number;
}

interface MortgageResults {
  monthlyPayment: number;
  totalPayment: number;
  totalInterest: number;
}

interface TaxResults {
  taxableIncome: number;
  estimatedTax: number;
  effectiveRate: number;
}

interface InputsByType {
  retirement: RetirementInputs;
  mortgage: MortgageInputs;
  tax: TaxInputs;
}

interface ResultsByType {
  retirement: RetirementResults | null;
  mortgage: MortgageResults | null;
  tax: TaxResults | null;
}

interface ModalState {
  mode: ModalMode;
  scenarioId: string | null;
  name: string;
  notes: string;
}

const RETIREMENT_DEFAULTS: RetirementInputs = {
  currentAge: 35,
  retirementAge: 65,
  currentSavings: 85000,
  annualIncome: 95000,
  monthlySavings: 1200,
};

const MORTGAGE_DEFAULTS: MortgageInputs = {
  homePrice: 425000,
  downPayment: 85000,
  interestRate: 6.5,
  loanTermYears: 30,
};

const TAX_DEFAULTS: TaxInputs = {
  grossIncome: 110000,
  deductions: 18000,
};

const TABS: Array<{ id: CalculatorType; label: string }> = [
  { id: 'retirement', label: 'Retirement' },
  { id: 'mortgage', label: 'Mortgage' },
  { id: 'tax', label: 'Tax' },
];

const FIELD_CONFIG: Record<
  CalculatorType,
  Array<{ key: string; label: string; step?: string; min?: number }>
> = {
  retirement: [
    { key: 'currentAge', label: 'Current Age', step: '1', min: 0 },
    { key: 'retirementAge', label: 'Retirement Age', step: '1', min: 0 },
    { key: 'currentSavings', label: 'Current Savings', step: '1000', min: 0 },
    { key: 'annualIncome', label: 'Annual Income', step: '1000', min: 0 },
    { key: 'monthlySavings', label: 'Monthly Savings', step: '100', min: 0 },
  ],
  mortgage: [
    { key: 'homePrice', label: 'Home Price', step: '1000', min: 0 },
    { key: 'downPayment', label: 'Down Payment', step: '1000', min: 0 },
    { key: 'interestRate', label: 'Interest Rate', step: '0.1', min: 0 },
    { key: 'loanTermYears', label: 'Loan Term (Years)', step: '1', min: 1 },
  ],
  tax: [
    { key: 'grossIncome', label: 'Gross Income', step: '1000', min: 0 },
    { key: 'deductions', label: 'Deductions', step: '1000', min: 0 },
  ],
};

function createDefaultInputs(): InputsByType {
  return {
    retirement: { ...RETIREMENT_DEFAULTS },
    mortgage: { ...MORTGAGE_DEFAULTS },
    tax: { ...TAX_DEFAULTS },
  };
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatFileName(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'scenario';
}

function cloneRecord<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function calculateRetirement(inputs: RetirementInputs): RetirementResults {
  const yearsToRetirement = Math.max(inputs.retirementAge - inputs.currentAge, 0);
  const projectedSavings =
    inputs.currentSavings + inputs.monthlySavings * 12 * yearsToRetirement;
  const totalContributions = inputs.monthlySavings * 12 * yearsToRetirement;

  return {
    yearsToRetirement,
    projectedSavings,
    annualIncome: inputs.annualIncome,
    totalContributions,
  };
}

function calculateMortgage(inputs: MortgageInputs): MortgageResults {
  const principal = Math.max(inputs.homePrice - inputs.downPayment, 0);
  const monthlyRate = inputs.interestRate / 100 / 12;
  const numberOfPayments = Math.max(inputs.loanTermYears * 12, 1);
  const monthlyPayment =
    monthlyRate === 0
      ? principal / numberOfPayments
      : (principal * monthlyRate * Math.pow(1 + monthlyRate, numberOfPayments)) /
        (Math.pow(1 + monthlyRate, numberOfPayments) - 1);
  const totalPayment = monthlyPayment * numberOfPayments;
  const totalInterest = totalPayment - principal;

  return {
    monthlyPayment,
    totalPayment,
    totalInterest,
  };
}

function calculateTax(inputs: TaxInputs): TaxResults {
  const taxableIncome = Math.max(inputs.grossIncome - inputs.deductions, 0);
  const estimatedTax = taxableIncome * 0.22;

  return {
    taxableIncome,
    estimatedTax,
    effectiveRate: taxableIncome === 0 ? 0 : (estimatedTax / taxableIncome) * 100,
  };
}

function getResultEntries(
  calculatorType: CalculatorType,
  results: RetirementResults | MortgageResults | TaxResults | null,
): Array<{ label: string; value: string }> {
  if (!results) return [];

  if (calculatorType === 'retirement') {
    const typedResults = results as RetirementResults;
    return [
      { label: 'Years to Retirement', value: `${typedResults.yearsToRetirement}` },
      { label: 'Projected Savings', value: formatCurrency(typedResults.projectedSavings) },
      { label: 'Annual Income', value: formatCurrency(typedResults.annualIncome) },
      { label: 'Total Contributions', value: formatCurrency(typedResults.totalContributions) },
    ];
  }

  if (calculatorType === 'mortgage') {
    const typedResults = results as MortgageResults;
    return [
      { label: 'Monthly Payment', value: formatCurrency(typedResults.monthlyPayment) },
      { label: 'Total Payment', value: formatCurrency(typedResults.totalPayment) },
      { label: 'Total Interest', value: formatCurrency(typedResults.totalInterest) },
    ];
  }

  const typedResults = results as TaxResults;
  return [
    { label: 'Taxable Income', value: formatCurrency(typedResults.taxableIncome) },
    { label: 'Estimated Tax', value: formatCurrency(typedResults.estimatedTax) },
    { label: 'Effective Rate', value: `${typedResults.effectiveRate.toFixed(1)}%` },
  ];
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

  pdf.save(`${formatFileName(scenario.name)}_${scenario.created_at.slice(0, 10)}.pdf`);
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
  if (!modalState.mode) return null;

  const title =
    modalState.mode === 'save'
      ? 'Save this scenario'
      : modalState.mode === 'rename'
        ? 'Rename scenario'
        : 'Duplicate scenario';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
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

          <div>
            <label htmlFor="scenario-notes" className="mb-2 block text-sm font-medium text-slate-700">
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

const EnhancedCalculator: React.FC = () => {
  const [activeTab, setActiveTab] = useState<CalculatorType>('retirement');
  const [viewMode, setViewMode] = useState<ViewMode>('calculator');
  const [inputsByType, setInputsByType] = useState<InputsByType>(createDefaultInputs);
  const [resultsByType, setResultsByType] = useState<ResultsByType>({
    retirement: null,
    mortgage: null,
    tax: null,
  });
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [message, setMessage] = useState<string>('');
  const [modalState, setModalState] = useState<ModalState>({
    mode: null,
    scenarioId: null,
    name: '',
    notes: '',
  });

  useEffect(() => {
    setScenarios(loadScenarios());
  }, []);

  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(() => setMessage(''), 3500);
    return () => window.clearTimeout(timer);
  }, [message]);

  const currentInputs = inputsByType[activeTab];
  const currentResults = resultsByType[activeTab];
  const resultEntries = useMemo(
    () => getResultEntries(activeTab, currentResults),
    [activeTab, currentResults],
  );

  const refreshScenarios = () => {
    setScenarios(loadScenarios());
  };

  const handleInputChange = (field: string, rawValue: string) => {
    const numericValue = Number(rawValue);
    setInputsByType((previous) => ({
      ...previous,
      [activeTab]: {
        ...previous[activeTab],
        [field]: Number.isNaN(numericValue) ? 0 : numericValue,
      },
    }));
  };

  const handleCalculate = () => {
    if (activeTab === 'retirement') {
      setResultsByType((previous) => ({
        ...previous,
        retirement: calculateRetirement(inputsByType.retirement),
      }));
      return;
    }

    if (activeTab === 'mortgage') {
      setResultsByType((previous) => ({
        ...previous,
        mortgage: calculateMortgage(inputsByType.mortgage),
      }));
      return;
    }

    setResultsByType((previous) => ({
      ...previous,
      tax: calculateTax(inputsByType.tax),
    }));
  };

  const handleSaveRequest = () => {
    setModalState({
      mode: 'save',
      scenarioId: null,
      name: `${TABS.find((tab) => tab.id === activeTab)?.label} Scenario`,
      notes: '',
    });
  };

  const closeModal = () => {
    setModalState({
      mode: null,
      scenarioId: null,
      name: '',
      notes: '',
    });
  };

  const handleModalSubmit = () => {
    if (!modalState.mode || !modalState.name.trim()) return;

    if (modalState.mode === 'save') {
      const scenario = saveScenario({
        calculator_type: activeTab,
        name: modalState.name,
        notes: modalState.notes,
        inputs: cloneRecord(currentInputs),
        outputs: cloneRecord(currentResults ?? {}),
      });
      refreshScenarios();
      setMessage(`Scenario saved: ${scenario.name}`);
      closeModal();
      return;
    }

    if (!modalState.scenarioId) return;

    if (modalState.mode === 'rename') {
      const updated = updateScenario(modalState.scenarioId, {
        name: modalState.name,
        notes: modalState.notes,
      });
      if (updated) {
        refreshScenarios();
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

  const handleLoadScenario = (scenario: Scenario) => {
    const calculatorType = scenario.calculator_type as CalculatorType;
    setActiveTab(calculatorType);
    setInputsByType((previous) => ({
      ...previous,
      [calculatorType]: cloneRecord(scenario.inputs) as InputsByType[CalculatorType],
    }));
    setResultsByType((previous) => ({
      ...previous,
      [calculatorType]: cloneRecord(scenario.outputs) as ResultsByType[CalculatorType],
    }));
    setViewMode('calculator');
    setMessage(`Scenario loaded: ${scenario.name}`);
  };

  const handleDuplicateScenario = (scenario: Scenario) => {
    setModalState({
      mode: 'duplicate',
      scenarioId: scenario.scenario_id,
      name: `${scenario.name} - Copy`,
      notes: scenario.notes,
    });
  };

  const handleRenameScenario = (scenario: Scenario) => {
    setModalState({
      mode: 'rename',
      scenarioId: scenario.scenario_id,
      name: scenario.name,
      notes: scenario.notes,
    });
  };

  const handleDeleteScenario = (scenarioId: string) => {
    if (!window.confirm('Are you sure? This cannot be undone.')) return;
    deleteScenario(scenarioId);
    refreshScenarios();
    setMessage('Scenario deleted.');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-slate-900">Enhanced Calculator</h1>
              <p className="mt-2 text-sm text-slate-500">
                Build and save retirement, mortgage, and tax scenarios in localStorage.
              </p>
            </div>
            {viewMode === 'calculator' ? (
              <Link
                to="/scenarios"
                className="inline-flex items-center rounded-xl border border-blue-200 bg-white px-4 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
              >
                <FolderOpen className="mr-2 h-4 w-4" />
                Scenario Management
              </Link>
            ) : (
              <button
                type="button"
                onClick={() => setViewMode('calculator')}
                className="inline-flex items-center rounded-xl border border-blue-200 bg-white px-4 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
              >
                <FolderOpen className="mr-2 h-4 w-4" />
                Back to Calculator
              </button>
            )}
          </div>

          {message && (
            <div className="mt-5 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm font-medium text-green-800">
              {message}
            </div>
          )}
        </div>

        {viewMode === 'calculator' ? (
          <div className="mt-6 space-y-6">
            <div className="flex flex-wrap gap-3">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">
                    {TABS.find((tab) => tab.id === activeTab)?.label} Calculator
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Enter your values and click calculate to produce results.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleCalculate}
                  className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700"
                >
                  <Calculator className="mr-2 h-4 w-4" />
                  Calculate
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {FIELD_CONFIG[activeTab].map((field) => (
                  <label key={field.key} className="block">
                    <span className="mb-2 block text-sm font-medium text-slate-700">
                      {field.label}
                    </span>
                    <input
                      type="number"
                      step={field.step}
                      min={field.min}
                      value={String((currentInputs as Record<string, number>)[field.key] ?? '')}
                      onChange={(event) => handleInputChange(field.key, event.target.value)}
                      className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    />
                  </label>
                ))}
              </div>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm">
              <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Results</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Results appear after calculation and can be saved as scenarios.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleSaveRequest}
                  disabled={!currentResults}
                  className="inline-flex items-center rounded-xl bg-green-600 px-5 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save this scenario
                </button>
              </div>

              {currentResults ? (
                <div className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
                  <div className="grid gap-4 md:grid-cols-2">
                    {resultEntries.map((entry) => (
                      <div key={entry.label} className="rounded-xl bg-white/80 p-4">
                        <p className="text-sm font-medium text-slate-500">{entry.label}</p>
                        <p className="mt-2 text-2xl font-semibold text-blue-900">{entry.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
                  No results yet. Click Calculate to generate them.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-3xl bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">My Scenarios</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Load, duplicate, rename, export, or delete your saved scenarios.
                </p>
              </div>
            </div>

            {scenarios.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
                No saved scenarios yet.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 md:grid-cols-[2fr_1fr_1fr_2fr]">
                  <span>Name</span>
                  <span>Type</span>
                  <span>Date Created</span>
                  <span>Actions</span>
                </div>

                {scenarios.map((scenario) => (
                  <div
                    key={scenario.scenario_id}
                    className="grid gap-4 rounded-2xl border border-slate-200 px-4 py-4 md:grid-cols-[2fr_1fr_1fr_2fr] md:items-center"
                  >
                    <div>
                      <p className="font-semibold text-slate-900">{scenario.name}</p>
                      {scenario.notes && (
                        <p className="mt-1 text-sm text-slate-500">{scenario.notes}</p>
                      )}
                    </div>
                    <p className="text-sm text-slate-700">{scenario.calculator_type}</p>
                    <p className="text-sm text-slate-700">{formatDate(scenario.created_at)}</p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => handleLoadScenario(scenario)}
                        className="rounded-xl bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                      >
                        Load
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDuplicateScenario(scenario)}
                        className="inline-flex items-center rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        Duplicate
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRenameScenario(scenario)}
                        className="inline-flex items-center rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Pencil className="mr-2 h-4 w-4" />
                        Rename
                      </button>
                      <button
                        type="button"
                        onClick={() => exportScenarioPdf(scenario)}
                        className="inline-flex items-center rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Export
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteScenario(scenario.scenario_id)}
                        className="inline-flex items-center rounded-xl border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <ScenarioModal
        modalState={modalState}
        onClose={closeModal}
        onChange={setModalState}
        onSubmit={handleModalSubmit}
      />
    </div>
  );
};

export default EnhancedCalculator;
