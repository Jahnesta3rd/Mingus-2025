import React, { useCallback, useState } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

type OilBucket = 'recent' | '3-6mo' | '6-12mo' | 'over_year' | 'unknown';
type MajorServiceStatus = 'up_to_date' | 'overdue' | 'scheduled' | 'unknown';
type Field =
  | 'make'
  | 'model'
  | 'year'
  | 'mileage'
  | 'monthly_payment'
  | 'insurance_monthly'
  | 'last_oil_change_bucket'
  | 'major_service_status'
  | 'known_issues';
type FieldErrors = Partial<Record<Field, string>>;

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { error?: string; message?: string };
    return j.error || j.message || text || res.statusText;
  } catch {
    return text || res.statusText || 'Request failed';
  }
}

function firstOfNextMonthIso(): string {
  const now = new Date();
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  next.setHours(12, 0, 0, 0);
  return next.toISOString().slice(0, 10);
}

export default function VehicleStep({ initialData, onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const currentYear = new Date().getFullYear();
  const [hasVehicle, setHasVehicle] = useState<boolean>(
    typeof initialData.has_vehicle === 'boolean' ? initialData.has_vehicle : true
  );
  const [make, setMake] = useState<string>(typeof initialData.make === 'string' ? initialData.make : '');
  const [model, setModel] = useState<string>(typeof initialData.model === 'string' ? initialData.model : '');
  const [year, setYear] = useState<string>(
    typeof initialData.year === 'number'
      ? String(initialData.year)
      : typeof initialData.year === 'string'
        ? initialData.year
        : ''
  );
  const [mileage, setMileage] = useState<string>(
    typeof initialData.mileage === 'number'
      ? String(initialData.mileage)
      : typeof initialData.mileage === 'string'
        ? initialData.mileage
        : ''
  );
  const [monthlyPayment, setMonthlyPayment] = useState<string>(
    typeof initialData.monthly_payment === 'number'
      ? String(initialData.monthly_payment)
      : typeof initialData.monthly_payment === 'string'
        ? initialData.monthly_payment
        : ''
  );
  const [insuranceMonthly, setInsuranceMonthly] = useState<string>(
    typeof initialData.insurance_monthly === 'number'
      ? String(initialData.insurance_monthly)
      : typeof initialData.insurance_monthly === 'string'
        ? initialData.insurance_monthly
        : ''
  );
  const [lastOilChangeBucket, setLastOilChangeBucket] = useState<OilBucket>(
    typeof initialData.last_oil_change_bucket === 'string'
      ? (initialData.last_oil_change_bucket as OilBucket)
      : 'unknown'
  );
  const [majorServiceStatus, setMajorServiceStatus] = useState<MajorServiceStatus>(
    typeof initialData.major_service_status === 'string'
      ? (initialData.major_service_status as MajorServiceStatus)
      : 'unknown'
  );
  const [knownIssues, setKnownIssues] = useState<string>(
    typeof initialData.known_issues === 'string' ? initialData.known_issues : ''
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  const [showValidationSummary, setShowValidationSummary] = useState(false);
  const [submitBanner, setSubmitBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearValidationFeedback = useCallback(() => {
    setErrors({});
    setShowValidationSummary(false);
  }, []);

  const validate = useCallback((): FieldErrors => {
    const next: FieldErrors = {};
    if (!make.trim()) next.make = 'Enter make.';
    if (!model.trim()) next.model = 'Enter model.';
    const y = Number.parseInt(year, 10);
    if (!Number.isInteger(y) || y < 1980 || y > currentYear + 1) {
      next.year = `Enter a year between 1980 and ${currentYear + 1}.`;
    }
    const mi = Number.parseInt(mileage, 10);
    if (!Number.isInteger(mi) || mi < 0) next.mileage = 'Mileage must be 0 or greater.';
    const mp = Number.parseFloat(monthlyPayment);
    if (!Number.isFinite(mp) || mp < 0) next.monthly_payment = 'Monthly payment must be 0 or greater.';
    const ins = Number.parseFloat(insuranceMonthly);
    if (!Number.isFinite(ins) || ins < 0) next.insurance_monthly = 'Insurance must be 0 or greater.';
    if (!['recent', '3-6mo', '6-12mo', 'over_year', 'unknown'].includes(lastOilChangeBucket)) {
      next.last_oil_change_bucket = 'Choose an option.';
    }
    if (!['up_to_date', 'overdue', 'scheduled', 'unknown'].includes(majorServiceStatus)) {
      next.major_service_status = 'Choose an option.';
    }
    if (knownIssues.length > 500) next.known_issues = 'Known issues must be 500 characters or fewer.';
    return next;
  }, [make, model, year, mileage, monthlyPayment, insuranceMonthly, lastOilChangeBucket, majorServiceStatus, knownIssues, currentYear]);

  const postVehicle = useCallback(
    async (payload: Record<string, unknown>) => {
      const res = await fetch('/api/modular-onboarding/commit-module', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({ module_id: 'vehicle', data: payload }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
    },
    [getAccessToken]
  );

  const postRecurringExpense = useCallback(
    async (label: 'Car Payment' | 'Auto Insurance', amount: number) => {
      const res = await fetch('/api/transaction-schedule/expenses', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({
          label,
          amount,
          category: 'transportation',
          frequency: 'monthly',
          due_day: 1,
          next_date: firstOfNextMonthIso(),
        }),
      });
      if (res.status !== 200 && res.status !== 201) {
        throw new Error(await readErrorMessage(res));
      }
    },
    [getAccessToken]
  );

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);
    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (!hasVehicle) {
        await postVehicle({ has_vehicle: false, vehicle_count: 0, vehicles: [] });
        await onSubmit({ has_vehicle: false });
        return;
      }

      const nextErrors = validate();
      setErrors(nextErrors);
      const order: Field[] = [
        'make',
        'model',
        'year',
        'mileage',
        'monthly_payment',
        'insurance_monthly',
        'last_oil_change_bucket',
        'major_service_status',
        'known_issues',
      ];
      const firstInvalid = order.find((f) => nextErrors[f]);
      if (firstInvalid) {
        setShowValidationSummary(true);
        const el = document.getElementById(`vehicle-${firstInvalid}`);
        el?.focus();
        return;
      }

      setShowValidationSummary(false);
      const parsedYear = Number.parseInt(year, 10);
      const parsedMileage = Number.parseInt(mileage, 10);
      const parsedPayment = Number.parseFloat(monthlyPayment);
      const parsedInsurance = Number.parseFloat(insuranceMonthly);
      const payload = {
        has_vehicle: true,
        vehicle_count: 1,
        make: make.trim(),
        model: model.trim(),
        year: parsedYear,
        mileage: parsedMileage,
        monthly_payment: parsedPayment,
        insurance_monthly: parsedInsurance,
        last_oil_change_bucket: lastOilChangeBucket,
        major_service_status: majorServiceStatus,
        known_issues: knownIssues.trim(),
        vehicles: [
          {
            make: make.trim(),
            model: model.trim(),
            year: parsedYear,
            monthly_payment: parsedPayment,
            monthly_fuel: parsedInsurance,
            recent_maintenance: lastOilChangeBucket === 'recent' || majorServiceStatus === 'up_to_date',
          },
        ],
      };
      await postVehicle(payload);
      if (parsedPayment > 0) await postRecurringExpense('Car Payment', parsedPayment);
      if (parsedInsurance > 0) await postRecurringExpense('Auto Insurance', parsedInsurance);
      await onSubmit({
        has_vehicle: true,
        has_payment: parsedPayment > 0,
        has_insurance: parsedInsurance > 0,
      });
    } catch (err) {
      setSubmitBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Vehicle</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add your vehicle details so we can project transportation costs and maintenance risk.
        </p>

        {showValidationSummary && Object.keys(errors).length > 0 && (
          <div className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white" role="alert">
            Please fix the highlighted errors below before continuing.
          </div>
        )}
        {submitBanner && (
          <div className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white" role="alert">
            <button
              type="button"
              className="absolute right-2 top-2 rounded p-1 text-white hover:bg-red-700"
              aria-label="Dismiss error"
              onClick={() => setSubmitBanner(null)}
            >
              ×
            </button>
            <span className="pr-8">{submitBanner}</span>
          </div>
        )}

        <div className="mt-6 space-y-4">
          <fieldset>
            <legend className={labelClass}>Do you currently have a vehicle?</legend>
            <div className="flex gap-4 text-sm text-[#1E293B]">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={hasVehicle}
                  onChange={() => {
                    clearValidationFeedback();
                    setHasVehicle(true);
                  }}
                />
                Yes
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={!hasVehicle}
                  onChange={() => {
                    clearValidationFeedback();
                    setHasVehicle(false);
                  }}
                />
                No
              </label>
            </div>
          </fieldset>

          {hasVehicle && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className={labelClass} htmlFor="vehicle-make">Make *</label>
                <input id="vehicle-make" className={inputClass} value={make} onChange={(e) => { clearValidationFeedback(); setMake(e.target.value); }} />
                {errors.make && <p className="mt-1 text-sm text-red-600">{errors.make}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-model">Model *</label>
                <input id="vehicle-model" className={inputClass} value={model} onChange={(e) => { clearValidationFeedback(); setModel(e.target.value); }} />
                {errors.model && <p className="mt-1 text-sm text-red-600">{errors.model}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-year">Year *</label>
                <input id="vehicle-year" className={inputClass} inputMode="numeric" value={year} onChange={(e) => { clearValidationFeedback(); setYear(e.target.value.replace(/\D/g, '').slice(0, 4)); }} />
                {errors.year && <p className="mt-1 text-sm text-red-600">{errors.year}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-mileage">Mileage *</label>
                <input id="vehicle-mileage" className={inputClass} inputMode="numeric" value={mileage} onChange={(e) => { clearValidationFeedback(); setMileage(e.target.value.replace(/\D/g, '')); }} />
                {errors.mileage && <p className="mt-1 text-sm text-red-600">{errors.mileage}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-monthly_payment">Monthly payment *</label>
                <input id="vehicle-monthly_payment" className={inputClass} type="number" min={0} step="0.01" value={monthlyPayment} onChange={(e) => { clearValidationFeedback(); setMonthlyPayment(e.target.value); }} />
                {errors.monthly_payment && <p className="mt-1 text-sm text-red-600">{errors.monthly_payment}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-insurance_monthly">Insurance monthly *</label>
                <input id="vehicle-insurance_monthly" className={inputClass} type="number" min={0} step="0.01" value={insuranceMonthly} onChange={(e) => { clearValidationFeedback(); setInsuranceMonthly(e.target.value); }} />
                {errors.insurance_monthly && <p className="mt-1 text-sm text-red-600">{errors.insurance_monthly}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-last_oil_change_bucket">Last oil change *</label>
                <select id="vehicle-last_oil_change_bucket" className={inputClass} value={lastOilChangeBucket} onChange={(e) => { clearValidationFeedback(); setLastOilChangeBucket(e.target.value as OilBucket); }}>
                  <option value="recent">Recent</option>
                  <option value="3-6mo">3–6 months</option>
                  <option value="6-12mo">6–12 months</option>
                  <option value="over_year">Over a year</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-major_service_status">Major service status *</label>
                <select id="vehicle-major_service_status" className={inputClass} value={majorServiceStatus} onChange={(e) => { clearValidationFeedback(); setMajorServiceStatus(e.target.value as MajorServiceStatus); }}>
                  <option value="up_to_date">Up to date</option>
                  <option value="overdue">Overdue</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className={labelClass} htmlFor="vehicle-known_issues">Known issues (optional, max 500)</label>
                <textarea id="vehicle-known_issues" className={inputClass} maxLength={500} value={knownIssues} onChange={(e) => { clearValidationFeedback(); setKnownIssues(e.target.value); }} />
                {errors.known_issues && <p className="mt-1 text-sm text-red-600">{errors.known_issues}</p>}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end sm:gap-4">
        <button
          type="button"
          onClick={() => onSkip()}
          className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 sm:w-auto sm:px-4"
        >
          Skip for now
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50 sm:w-auto sm:min-w-[200px]"
        >
          {isSubmitting ? 'Saving…' : 'Save and continue'}
        </button>
      </div>
    </form>
  );
}
