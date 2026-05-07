import React, { useCallback, useState } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

type Field = 'current_position' | 'employer' | 'industry' | 'years_in_role' | 'next_review_date';
type FieldErrors = Partial<Record<Field, string>>;

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';
const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Education',
  'Finance',
  'Government',
  'Retail',
  'Manufacturing',
  'Hospitality',
  'Construction',
  'Other',
];

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

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function CareerStep({ initialData, onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [currentPosition, setCurrentPosition] = useState<string>(
    typeof initialData.current_position === 'string' ? initialData.current_position : ''
  );
  const [employer, setEmployer] = useState<string>(
    typeof initialData.employer === 'string' ? initialData.employer : ''
  );
  const [industry, setIndustry] = useState<string>(
    typeof initialData.industry === 'string' ? initialData.industry : ''
  );
  const [yearsInRole, setYearsInRole] = useState<string>(
    typeof initialData.years_in_role === 'number'
      ? String(initialData.years_in_role)
      : typeof initialData.years_in_role === 'string'
        ? initialData.years_in_role
        : ''
  );
  const [nextReviewDate, setNextReviewDate] = useState<string>(
    typeof initialData.next_review_date === 'string' ? initialData.next_review_date : ''
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
    if (!currentPosition.trim()) next.current_position = 'Current position is required.';
    if (!employer.trim()) next.employer = 'Employer is required.';
    if (!industry.trim()) next.industry = 'Choose an industry.';
    const years = Number.parseInt(yearsInRole, 10);
    if (!Number.isInteger(years) || years < 0) next.years_in_role = 'Years in role must be 0 or greater.';
    if (nextReviewDate && nextReviewDate <= todayIso()) {
      next.next_review_date = 'Next review date must be in the future.';
    }
    return next;
  }, [currentPosition, employer, industry, yearsInRole, nextReviewDate]);

  const postCareer = useCallback(
    async (payload: Record<string, unknown>) => {
      const res = await fetch('/api/modular-onboarding/commit-module', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({ module_id: 'career', data: payload }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
    },
    [getAccessToken]
  );

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);
    const nextErrors = validate();
    setErrors(nextErrors);
    const order: Field[] = ['current_position', 'employer', 'industry', 'years_in_role', 'next_review_date'];
    const firstInvalid = order.find((f) => nextErrors[f]);
    if (firstInvalid) {
      setShowValidationSummary(true);
      const el = document.getElementById(`career-${firstInvalid}`);
      el?.focus();
      return;
    }
    setShowValidationSummary(false);

    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    setIsSubmitting(true);
    try {
      const years = Number.parseInt(yearsInRole, 10);
      await postCareer({
        current_position: currentPosition.trim(),
        employer: employer.trim(),
        industry,
        years_in_role: years,
        next_review_date: nextReviewDate || null,
        current_role: currentPosition.trim(),
        years_experience: years,
      });
      await onSubmit({ industry, years_in_role: years });
    } catch (err) {
      setSubmitBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Career</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Tell us where you are in your career so we can personalize your planning guidance.
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

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-current_position">Current position *</label>
            <input id="career-current_position" className={inputClass} value={currentPosition} onChange={(e) => { clearValidationFeedback(); setCurrentPosition(e.target.value); }} />
            {errors.current_position && <p className="mt-1 text-sm text-red-600">{errors.current_position}</p>}
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-employer">Employer *</label>
            <input id="career-employer" className={inputClass} value={employer} onChange={(e) => { clearValidationFeedback(); setEmployer(e.target.value); }} />
            {errors.employer && <p className="mt-1 text-sm text-red-600">{errors.employer}</p>}
          </div>
          <div>
            <label className={labelClass} htmlFor="career-industry">Industry *</label>
            <select id="career-industry" className={inputClass} value={industry} onChange={(e) => { clearValidationFeedback(); setIndustry(e.target.value); }}>
              <option value="">Select…</option>
              {INDUSTRIES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            {errors.industry && <p className="mt-1 text-sm text-red-600">{errors.industry}</p>}
          </div>
          <div>
            <label className={labelClass} htmlFor="career-years_in_role">Years in role *</label>
            <input id="career-years_in_role" className={inputClass} inputMode="numeric" value={yearsInRole} onChange={(e) => { clearValidationFeedback(); setYearsInRole(e.target.value.replace(/\D/g, '')); }} />
            {errors.years_in_role && <p className="mt-1 text-sm text-red-600">{errors.years_in_role}</p>}
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-next_review_date">Next review date (optional)</label>
            <input id="career-next_review_date" className={inputClass} type="date" value={nextReviewDate} onChange={(e) => { clearValidationFeedback(); setNextReviewDate(e.target.value); }} />
            {errors.next_review_date && <p className="mt-1 text-sm text-red-600">{errors.next_review_date}</p>}
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
