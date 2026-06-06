import React, { useCallback, useState } from 'react';
import { OCCUPATION_GROUPS } from '../../../../constants/occupationOptions';
import { useAuth } from '../../../../hooks/useAuth';
import CareerResumeUploadSection from '../../../career/CareerResumeUploadSection';
import {
  applyResumePrefill,
  type CareerResumePrefill,
} from '../../../career/careerResumeUpload';
import type { StepProps } from '../StepDefinitions';

type RelocationOpenness = 'yes' | 'maybe' | 'no';

type Field =
  | 'occupation_key'
  | 'current_position'
  | 'employer'
  | 'industry'
  | 'years_in_role'
  | 'next_review_date'
  | 'target_comp';
type FieldErrors = Partial<Record<Field, string>>;

function parseRelocationOpenness(raw: unknown): RelocationOpenness {
  if (raw === true || raw === 'yes') return 'yes';
  if (raw === 'maybe') return 'maybe';
  return 'no';
}

function relocationToOpenToMove(value: RelocationOpenness): boolean {
  return value === 'yes';
}

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

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function CareerStep({ initialData, onSubmit, onSkip }: StepProps) {
  const { getAccessToken } = useAuth();
  const [occupationKey, setOccupationKey] = useState<string>('');
  const [occupationTouched, setOccupationTouched] = useState<boolean>(false);
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
  const [satisfaction, setSatisfaction] = useState<number>(
    typeof initialData.satisfaction === 'number' && initialData.satisfaction >= 1 && initialData.satisfaction <= 5
      ? initialData.satisfaction
      : 3
  );
  const [relocationOpenness, setRelocationOpenness] = useState<RelocationOpenness>(
    parseRelocationOpenness(initialData.open_to_move)
  );
  const [targetComp, setTargetComp] = useState<string>(
    typeof initialData.target_comp === 'number'
      ? String(initialData.target_comp)
      : typeof initialData.target_comp === 'string'
        ? initialData.target_comp
        : ''
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  const [showValidationSummary, setShowValidationSummary] = useState(false);
  const [submitBanner, setSubmitBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadSectionDismissed, setUploadSectionDismissed] = useState(false);

  const handleResumePrefill = useCallback(
    (prefill: CareerResumePrefill) => {
      const merged = applyResumePrefill(
        {
          title: currentPosition,
          employer,
          industry,
          yearsExperience: yearsInRole,
        },
        prefill
      );

      if (merged.title != null && merged.title !== currentPosition) {
        setCurrentPosition(String(merged.title));
      }
      if (merged.employer != null && merged.employer !== employer) {
        setEmployer(String(merged.employer));
      }
      if (merged.industry != null && merged.industry !== industry) {
        setIndustry(String(merged.industry));
      }
      if (merged.yearsExperience != null && merged.yearsExperience !== yearsInRole) {
        setYearsInRole(String(merged.yearsExperience));
      }
    },
    [currentPosition, employer, industry, yearsInRole]
  );

  const clearValidationFeedback = useCallback(() => {
    setErrors({});
    setShowValidationSummary(false);
  }, []);

  const validate = useCallback((): FieldErrors => {
    const next: FieldErrors = {};
    if (!occupationTouched) next.occupation_key = 'Please select an occupation.';
    if (!industry.trim()) next.industry = 'Choose an industry.';
    const years = Number.parseInt(yearsInRole, 10);
    if (!Number.isInteger(years) || years < 0) next.years_in_role = 'Years in role must be 0 or greater.';
    if (nextReviewDate && nextReviewDate <= todayIso()) {
      next.next_review_date = 'Next review date must be in the future.';
    }
    if (targetComp.trim()) {
      const tc = Number.parseFloat(targetComp);
      if (!Number.isFinite(tc) || tc < 0) {
        next.target_comp = 'Target compensation must be 0 or greater.';
      }
    }
    return next;
  }, [occupationTouched, industry, yearsInRole, nextReviewDate, targetComp]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);
    const nextErrors = validate();
    setErrors(nextErrors);
    const order: Field[] = [
      'occupation_key',
      'current_position',
      'employer',
      'industry',
      'years_in_role',
      'next_review_date',
      'target_comp',
    ];
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
      const parsedTarget = targetComp.trim() ? Number.parseFloat(targetComp) : null;
      await onSubmit({
        occupation_key: occupationKey === '' ? null : occupationKey,
        current_role: currentPosition.trim() || null,
        industry,
        years_experience: years,
        satisfaction,
        open_to_move: relocationToOpenToMove(relocationOpenness),
        target_comp: parsedTarget,
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

        {!uploadSectionDismissed && (
          <div className="mt-6">
            <CareerResumeUploadSection
              onPrefill={handleResumePrefill}
              showSkipLink
              manualFieldsAnchorId="career-manual-fields"
              onSkipManual={() => setUploadSectionDismissed(true)}
              variant="onboarding"
            />
          </div>
        )}

        <div id="career-manual-fields" className="mt-6 grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-occupation_key">Occupation *</label>
            <select
              id="career-occupation_key"
              className={inputClass}
              value={occupationKey}
              onChange={(e) => {
                clearValidationFeedback();
                setOccupationKey(e.target.value);
                setOccupationTouched(true);
                setErrors((prev) => ({ ...prev, occupation_key: undefined }));
              }}
            >
              <option value="" disabled={!occupationTouched}>
                Select your occupation…
              </option>
              {OCCUPATION_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </optgroup>
              ))}
              <option value="">Other / not listed</option>
            </select>
            {errors.occupation_key && (
              <p className="mt-1 text-sm text-red-600">{errors.occupation_key}</p>
            )}
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-current_position">Specific title (optional)</label>
            <input id="career-current_position" className={inputClass} value={currentPosition} onChange={(e) => { clearValidationFeedback(); setCurrentPosition(e.target.value); }} />
            {errors.current_position && <p className="mt-1 text-sm text-red-600">{errors.current_position}</p>}
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-employer">Employer (optional)</label>
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
            <label className={labelClass} htmlFor="career-satisfaction">
              How satisfied are you with your current role? (1–5)
            </label>
            <div className="flex items-center gap-3">
              <input
                id="career-satisfaction"
                className="min-h-11 flex-1 accent-[#5B2D8E]"
                type="range"
                min={1}
                max={5}
                step={1}
                value={satisfaction}
                onChange={(e) => {
                  clearValidationFeedback();
                  setSatisfaction(Number.parseInt(e.target.value, 10));
                }}
              />
              <span className="min-w-[3rem] text-sm font-medium text-[#1E293B]">{satisfaction}/5</span>
            </div>
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-open_to_move">
              Are you open to relocating for the right opportunity?
            </label>
            <select
              id="career-open_to_move"
              className={inputClass}
              value={relocationOpenness}
              onChange={(e) => {
                clearValidationFeedback();
                setRelocationOpenness(e.target.value as RelocationOpenness);
              }}
            >
              <option value="yes">Yes, definitely</option>
              <option value="maybe">Maybe, depends on the opportunity</option>
              <option value="no">No, prefer to stay in my area</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="career-target_comp">
              Target annual compensation (optional)
            </label>
            <input
              id="career-target_comp"
              className={inputClass}
              type="number"
              min={0}
              step={1000}
              placeholder="e.g., 120000"
              value={targetComp}
              onChange={(e) => {
                clearValidationFeedback();
                setTargetComp(e.target.value);
              }}
            />
            {errors.target_comp && <p className="mt-1 text-sm text-red-600">{errors.target_comp}</p>}
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
