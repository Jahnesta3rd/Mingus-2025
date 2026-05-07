import React, { useCallback, useState } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

type Ownership = 'rent' | 'own_with_mortgage' | 'own_outright' | 'family' | 'other';
type Field = 'ownership' | 'monthly_cost' | 'zip_code';
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

function mapHousingType(ownership: Ownership): 'rent' | 'own' {
  return ownership === 'rent' ? 'rent' : 'own';
}

export default function HousingStep({ initialData, onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [ownership, setOwnership] = useState<Ownership | ''>(
    typeof initialData.ownership === 'string' ? (initialData.ownership as Ownership) : ''
  );
  const [monthlyCost, setMonthlyCost] = useState<string>(
    typeof initialData.monthly_cost === 'number'
      ? String(initialData.monthly_cost)
      : typeof initialData.monthly_cost === 'string'
        ? initialData.monthly_cost
        : ''
  );
  const [includesUtilities, setIncludesUtilities] = useState<boolean>(
    typeof initialData.includes_utilities === 'boolean' ? initialData.includes_utilities : false
  );
  const [city, setCity] = useState<string>(typeof initialData.city === 'string' ? initialData.city : '');
  const [zipCode, setZipCode] = useState<string>(
    typeof initialData.zip_code === 'string' ? initialData.zip_code : ''
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
    if (!ownership) next.ownership = 'Choose a housing situation.';
    const requiresCost = ownership === 'rent' || ownership === 'own_with_mortgage';
    const amt = Number.parseFloat(monthlyCost);
    if (requiresCost && (!Number.isFinite(amt) || amt <= 0)) {
      next.monthly_cost = 'Enter a monthly cost greater than zero.';
    }
    if (zipCode.trim() && !/^\d{5}$/.test(zipCode.trim())) {
      next.zip_code = 'ZIP code must be 5 digits.';
    }
    return next;
  }, [ownership, monthlyCost, zipCode]);

  const postRecurringExpense = useCallback(
    async (label: 'Rent' | 'Mortgage', amount: number) => {
      const res = await fetch('/api/transaction-schedule/expenses', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({
          label,
          amount,
          category: 'housing',
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
    const nextErrors = validate();
    setErrors(nextErrors);

    const order: Field[] = ['ownership', 'monthly_cost', 'zip_code'];
    const firstInvalid = order.find((f) => nextErrors[f]);
    if (firstInvalid) {
      setShowValidationSummary(true);
      const el = document.getElementById(`housing-${firstInvalid}`);
      el?.focus();
      return;
    }
    setShowValidationSummary(false);

    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    const parsedMonthly = Number.parseFloat(monthlyCost);
    const hasRecurring =
      (ownership === 'rent' || ownership === 'own_with_mortgage') &&
      Number.isFinite(parsedMonthly) &&
      parsedMonthly > 0;

    setIsSubmitting(true);
    try {
      if (hasRecurring) {
        await postRecurringExpense(ownership === 'rent' ? 'Rent' : 'Mortgage', parsedMonthly);
      }
      await onSubmit({
        housing_type: mapHousingType(ownership as Ownership),
        monthly_cost: hasRecurring ? parsedMonthly : 0,
        zip_or_city: city.trim() || zipCode.trim() || 'N/A',
        split_share_pct: 100,
        has_buy_goal: false,
        target_price: null,
        target_timeline_months: null,
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
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Housing</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Share your current housing setup so we can model recurring costs in your forecast.
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

        <div className="mt-6 space-y-5">
          <fieldset>
            <legend className={labelClass}>What best describes your housing? *</legend>
            <div className="space-y-2">
              {[
                { value: 'rent', label: 'Rent' },
                { value: 'own_with_mortgage', label: 'Own with mortgage' },
                { value: 'own_outright', label: 'Own outright' },
                { value: 'family', label: 'Living with family' },
                { value: 'other', label: 'Other' },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 text-sm text-[#1E293B]">
                  <input
                    id={opt.value === 'rent' ? 'housing-ownership' : undefined}
                    type="radio"
                    name="ownership"
                    value={opt.value}
                    checked={ownership === opt.value}
                    onChange={() => {
                      clearValidationFeedback();
                      setOwnership(opt.value as Ownership);
                    }}
                  />
                  {opt.label}
                </label>
              ))}
            </div>
            {errors.ownership && <p className="mt-1 text-sm text-red-600">{errors.ownership}</p>}
          </fieldset>

          {(ownership === 'rent' || ownership === 'own_with_mortgage') && (
            <div>
              <label className={labelClass} htmlFor="housing-monthly_cost">
                Monthly cost *
              </label>
              <input
                id="housing-monthly_cost"
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                value={monthlyCost}
                onChange={(e) => {
                  clearValidationFeedback();
                  setMonthlyCost(e.target.value);
                }}
              />
              {errors.monthly_cost && <p className="mt-1 text-sm text-red-600">{errors.monthly_cost}</p>}
            </div>
          )}

          {ownership === 'rent' && (
            <label className="flex items-center gap-2 text-sm text-[#1E293B]">
              <input
                type="checkbox"
                checked={includesUtilities}
                onChange={(e) => {
                  clearValidationFeedback();
                  setIncludesUtilities(e.target.checked);
                }}
              />
              Includes utilities
            </label>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="housing-city">
                City (optional)
              </label>
              <input
                id="housing-city"
                className={inputClass}
                value={city}
                onChange={(e) => {
                  clearValidationFeedback();
                  setCity(e.target.value);
                }}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="housing-zip_code">
                ZIP code (optional)
              </label>
              <input
                id="housing-zip_code"
                className={inputClass}
                inputMode="numeric"
                value={zipCode}
                onChange={(e) => {
                  clearValidationFeedback();
                  setZipCode(e.target.value.replace(/\D/g, '').slice(0, 5));
                }}
              />
              {errors.zip_code && <p className="mt-1 text-sm text-red-600">{errors.zip_code}</p>}
            </div>
          </div>
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
