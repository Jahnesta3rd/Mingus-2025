import React, { useCallback, useId, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, Loader2, Upload } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import {
  buildPrefillFromUploadResponse,
  hasNonEmptyParsed,
  type CareerResumePrefill,
  type CareerResumeUploadStatus,
  uploadCareerResume,
  validateResumeFile,
} from './careerResumeUpload';

const ACCEPT = '.pdf,.docx,.doc,.txt';

export interface CareerResumeUploadSectionProps {
  /** Called after a successful parse with extracted pre-fill values. */
  onPrefill?: (data: CareerResumePrefill) => void;
  /** When true, show dismissed banner instead of upload UI. */
  dismissed?: boolean;
  /** Restore upload UI after subsection skip. */
  onRestore?: () => void;
  /** Show "Skip resume upload →" (CareerStep onboarding). */
  showSkipLink?: boolean;
  /** Element id to scroll to when skip is clicked. */
  manualFieldsAnchorId?: string;
  /** Called when skip is clicked (e.g. dismiss upload section). */
  onSkipManual?: () => void;
  /** Visual variant for copy tweaks. */
  variant?: 'onboarding' | 'profile';
  className?: string;
}

export default function CareerResumeUploadSection({
  onPrefill,
  dismissed = false,
  onRestore,
  showSkipLink = false,
  manualFieldsAnchorId,
  onSkipManual,
  variant = 'onboarding',
  className = '',
}: CareerResumeUploadSectionProps) {
  const { getAccessToken } = useAuth();
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<CareerResumeUploadStatus>('idle');
  const [inlineError, setInlineError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setInlineError(null);
    if (status === 'network_error' || status === 'parse_error') {
      setStatus('idle');
    }
  };

  const handleUpload = useCallback(async () => {
    const validationError = validateResumeFile(selectedFile);
    if (validationError) {
      setInlineError(validationError);
      return;
    }

    setInlineError(null);
    setStatus('uploading');

    const result = await uploadCareerResume(selectedFile!, getAccessToken);

    if (!result.ok) {
      setStatus('network_error');
      return;
    }

    const { data } = result;

    if (data.success !== true) {
      setStatus('network_error');
      return;
    }

    if (data.parse_error || !hasNonEmptyParsed(data.parsed)) {
      setStatus('parse_error');
      return;
    }

    const prefill = buildPrefillFromUploadResponse(data);
    onPrefill?.(prefill);
    setStatus('success');
  }, [getAccessToken, onPrefill, selectedFile]);

  const handleReplace = () => {
    setStatus('idle');
    setSelectedFile(null);
    setInlineError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSkip = () => {
    onSkipManual?.();
    if (manualFieldsAnchorId) {
      document.getElementById(manualFieldsAnchorId)?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  };

  const inputDisabled = status === 'uploading' || status === 'success';
  const successMessage =
    variant === 'profile'
      ? 'Resume uploaded — your career profile has been updated'
      : 'Resume uploaded — fields pre-filled below';

  if (dismissed) {
    return (
      <section
        className={`rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-5 ${className}`}
        aria-label="Resume upload skipped"
      >
        <p className="text-sm text-[#64748B]">
          Upload skipped — you can add your resume later from your profile.
        </p>
        {onRestore && (
          <button
            type="button"
            onClick={onRestore}
            className="mt-2 text-sm font-medium text-[#5B2D8E] underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Show upload again →
          </button>
        )}
      </section>
    );
  }

  return (
    <section
      className={`rounded-xl border border-[#E2E8F0] bg-[#FAF5FF] p-5 ${className}`}
      aria-label="Resume upload"
    >
      <h2 className="text-base font-semibold text-[#1E293B]">Upload your resume (optional)</h2>
      <p className="mt-1 text-sm text-[#64748B]">
        We&apos;ll pre-fill your career details automatically
      </p>

      {status === 'success' && (
        <div
          className="mt-4 flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-800"
          role="status"
        >
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <div className="space-y-2">
            <span>{successMessage}</span>
            {variant === 'profile' && (
              <button
                type="button"
                onClick={handleReplace}
                className="block text-sm font-medium text-[#5B2D8E] underline-offset-2 hover:underline"
              >
                Upload a different resume
              </button>
            )}
          </div>
        </div>
      )}

      {status === 'parse_error' && (
        <div
          className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900"
          role="status"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <span>We couldn&apos;t read this resume. Fill in your details below.</span>
        </div>
      )}

      {status === 'network_error' && (
        <div
          className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
          role="alert"
        >
          Upload failed. Try again or fill in manually.
        </div>
      )}

      {status !== 'success' && (
        <div className="mt-4 space-y-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#1E293B]" htmlFor={inputId}>
              Resume file
            </label>
            <input
              ref={fileInputRef}
              id={inputId}
              type="file"
              accept={ACCEPT}
              disabled={inputDisabled}
              onChange={handleFileChange}
              className="block w-full text-sm text-[#64748B] file:mr-3 file:rounded-lg file:border-0 file:bg-[#5B2D8E] file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:opacity-95 disabled:opacity-50"
            />
            <p className="mt-1 text-xs text-[#64748B]">PDF, DOCX, DOC, or TXT · Max 5MB</p>
          </div>

          {inlineError && (
            <p className="text-sm text-red-600" role="alert">
              {inlineError}
            </p>
          )}

          <button
            type="button"
            disabled={status === 'uploading' || !selectedFile}
            onClick={() => void handleUpload()}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#5B2D8E] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === 'uploading' ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Uploading…
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" aria-hidden />
                Upload &amp; Auto-fill
              </>
            )}
          </button>
        </div>
      )}

      {showSkipLink && (
        <div className="mt-4">
          <button
            type="button"
            onClick={handleSkip}
            className="text-sm text-[#64748B] underline-offset-2 hover:text-[#1E293B] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Skip resume upload →
          </button>
          <p className="mt-1 text-xs text-[#94A3B8]">
            This only skips the upload. You can still fill in your career details below, or skip the
            whole step at the bottom.
          </p>
        </div>
      )}
    </section>
  );
}
