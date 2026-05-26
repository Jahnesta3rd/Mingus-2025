import React, { useCallback, useState } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

type Ownership = 'rent' | 'own_with_mortgage' | 'own_outright' | 'family' | 'other';
type Field = 'ownership' | 'monthly_cost' | 'zip_code' | 'has_buy_goal' | 'target_timeline_months';
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
  const [hasBuyGoal, setHasBuyGoal] = useState<'yes' | 'no' | ''>('');
  const [targetTimelineMonths, setTargetTimelineMonths] = useState<string>('');
  const [includesUtilities, setIncludesUtilities] = useState<boolean>(
    typeof initialData.includes_utilities === 'boolean' ? initialData.includes_utilities : false
  );
  const [sharesHousing, setSharesHousing] = useState<boolean>(() => {
    const pct = initialData.split_share_pct;
    if (typeof pct === 'number' && pct > 0 && pct < 100) return true;
    return initialData.shares_housing === true;
  });
  const [sharePercentage, setSharePercentage] = useState<string>(() => {
    const pct = initialData.split_share_pct;
    if (typeof pct === 'number' && pct > 0 && pct <= 100) return String(pct);
    if (typeof pct === 'string' && pct.trim()) return pct;
    return '';
  });
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
    if (!zipCode.trim()) {
      next.zip_code = 'ZIP code is required';
    } else if (!/^\d{5}$/.test(zipCode.trim())) {
      next.zip_code = 'ZIP code must be 5 digits';
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

    let splitSharePct = 100;
    if (sharesHousing) {
      const pct = Number.parseFloat(sharePercentage);
      if (!Number.isFinite(pct) || pct < 1 || pct > 100) {
        setErrors({ monthly_cost: 'Enter your share as a percentage from 1 to 100.' });
        setShowValidationSummary(true);
        document.getElementById('housing-share_percentage')?.focus();
        return;
      }
      splitSharePct = pct;
    }

    const effectiveMonthly =
      hasRecurring && sharesHousing ? parsedMonthly * (splitSharePct / 100) : parsedMonthly;

    if (hasBuyGoal === '') {
      setErrors((prev) => ({
        ...prev,
        has_buy_goal: "Please answer whether you're saving to buy a home.",
      }));
      setShowValidationSummary(true);
      return;
    }
    if (hasBuyGoal === 'yes') {
      if (targetTimelineMonths.trim() === '') {
        setErrors((prev) => ({
          ...prev,
          target_timeline_months: "Please enter how many months until you'd like to buy.",
        }));
        setShowValidationSummary(true);
        document.getElementById('housing-target_timeline_months')?.focus();
        return;
      }
      const months = Number.parseInt(targetTimelineMonths, 10);
      if (Number.isNaN(months) || months < 1 || months > 36) {
        setErrors((prev) => ({
          ...prev,
          target_timeline_months: 'Please enter a number of months between 1 and 36.',
        }));
        setShowValidationSummary(true);
        document.getElementById('housing-target_timeline_months')?.focus();
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (hasRecurring && effectiveMonthly > 0) {
        await postRecurringExpense(
          ownership === 'rent' ? 'Rent' : 'Mortgage',
          effectiveMonthly
        );
      }
      await onSubmit({
        housing_type: mapHousingType(ownership as Ownership),
        monthly_cost: hasRecurring ? parsedMonthly : 0,
        zip_or_city: zipCode.trim(),
        split_share_pct: splitSharePct,
        has_buy_goal: hasBuyGoal === 'yes',
        target_price: null,
        target_timeline_months: hasBuyGoal === 'yes' ? Number.parseInt(targetTimelineMonths, 10) : null,
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

          {(ownership === 'rent' || ownership === 'own_with_mortgage') && (
            <div className="space-y-3">
              <label className="flex items-center gap-2 text-sm text-[#1E293B]">
                <input
                  type="checkbox"
                  id="housing-shares_housing"
                  checked={sharesHousing}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setSharesHousing(e.target.checked);
                    if (!e.target.checked) setSharePercentage('');
                  }}
                />
                Do you share housing costs? (e.g., roommates, spouse)
              </label>
              {sharesHousing && (
                <>
                  <div>
                    <label className={labelClass} htmlFor="housing-share_percentage">
                      What % of the total housing cost do you pay? (1–100)
                    </label>
                    <input
                      id="housing-share_percentage"
                      className={inputClass}
                      type="number"
                      min={1}
                      max={100}
                      placeholder="e.g., 50"
                      value={sharePercentage}
                      onChange={(e) => {
                        clearValidationFeedback();
                        setSharePercentage(e.target.value);
                      }}
                    />
                  </div>
                  {Number.isFinite(Number.parseFloat(monthlyCost)) &&
                    Number.isFinite(Number.parseFloat(sharePercentage)) && (
                      <p className="text-sm text-[#64748B]">
                        Your estimated monthly cost:{' '}
                        <span className="font-medium text-[#1E293B]">
                          $
                          {(
                            Number.parseFloat(monthlyCost) *
                            (Number.parseFloat(sharePercentage) / 100)
                          ).toFixed(2)}
                        </span>
                      </p>
                    )}
                </>
              )}
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
                ZIP code *
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

          <fieldset>
            <legend className={labelClass}>Are you saving to buy a home in the next 3 years? *</legend>
            <div className="space-y-2">
              {[
                { value: 'yes', label: 'Yes' },
                { value: 'no', label: 'No' },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 text-sm text-[#1E293B]">
                  <input
                    type="radio"
                    name="has_buy_goal"
                    value={opt.value}
                    checked={hasBuyGoal === opt.value}
                    onChange={(e) => {
                      setHasBuyGoal(e.target.value as 'yes' | 'no');
                      if (e.target.value === 'no') setTargetTimelineMonths('');
                      setErrors((prev) => ({
                        ...prev,
                        has_buy_goal: undefined,
                        target_timeline_months: undefined,
                      }));
                    }}
                  />
                  {opt.label}
                </label>
              ))}
            </div>
            {errors.has_buy_goal && <p className="mt-1 text-sm text-red-600">{errors.has_buy_goal}</p>}
          </fieldset>

          {hasBuyGoal === 'yes' && (
            <div>
              <label className={labelClass} htmlFor="housing-target_timeline_months">
                How many months until you'd like to buy? *
              </label>
              <input
                id="housing-target_timeline_months"
                className={inputClass}
                type="number"
                min={1}
                max={36}
                step={1}
                inputMode="numeric"
                value={targetTimelineMonths}
                onChange={(e) => {
                  setTargetTimelineMonths(e.target.value);
                  setErrors((prev) => ({ ...prev, target_timeline_months: undefined }));
                }}
                placeholder="e.g. 18"
              />
              {errors.target_timeline_months && (
                <p className="mt-1 text-sm text-red-600">{errors.target_timeline_months}</p>
              )}
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
