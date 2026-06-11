import React, { useCallback, useEffect, useState } from 'react';
import EmployerSelect, { type EmployerSelectValue } from './EmployerSelect';
import {
  EMPLOYER_TYPE_OPTIONS,
  employerTypeHelperText,
  type EmployerType,
} from '../constants/employerTypes';
import { useAuth } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

const BACKFILL_DISMISSED_KEY = 'mingus_employer_backfill_dismissed';

const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';
const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';

export function isEmployerBackfillDismissed(): boolean {
  try {
    return localStorage.getItem(BACKFILL_DISMISSED_KEY) === 'true';
  } catch {
    return false;
  }
}

export function dismissEmployerBackfill(): void {
  try {
    localStorage.setItem(BACKFILL_DISMISSED_KEY, 'true');
  } catch {
    /* ignore */
  }
}

interface EmployerBackfillModalProps {
  onClose: () => void;
}

export default function EmployerBackfillModal({ onClose }: EmployerBackfillModalProps) {
  const { getAccessToken } = useAuth();
  const [employer, setEmployer] = useState<EmployerSelectValue | null>(null);
  const [employerType, setEmployerType] = useState<EmployerType | ''>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    const headers: Record<string, string> = {
      ...csrfHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    fetch('/api/user/profile', { credentials: 'include', headers })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const profile = data?.profile ?? data;
        const name =
          typeof profile?.employer_name_text === 'string'
            ? profile.employer_name_text
            : '';
        const cik =
          typeof profile?.employer_cik === 'string' ? profile.employer_cik : null;
        if (name) setEmployer({ cik, name });
        if (typeof profile?.employer_type === 'string') {
          setEmployerType(profile.employer_type as EmployerType);
        }
      })
      .finally(() => setLoading(false));
  }, [getAccessToken]);

  const handleDismiss = useCallback(() => {
    dismissEmployerBackfill();
    onClose();
  }, [onClose]);

  const handleSave = async () => {
    if (!employer?.name?.trim() || !employerType) {
      setError('Please enter your employer and select an employer type.');
      return;
    }
    setSaving(true);
    setError(null);
    const token = getAccessToken();
    try {
      const res = await fetch('/api/user/profile', {
        method: 'PATCH',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          employer_cik: employer.cik,
          employer_name_text: employer.name.trim(),
          employer_type: employerType,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || body.success === false) {
        setError("Couldn't save — try again");
        return;
      }
      dismissEmployerBackfill();
      onClose();
    } catch {
      setError("Couldn't save — try again");
    } finally {
      setSaving(false);
    }
  };

  const helper = employerTypeHelperText(employerType);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-900/60 p-0 sm:items-center sm:p-4"
      role="presentation"
      onClick={handleDismiss}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-md flex-col rounded-t-2xl border border-[#E2E8F0] bg-white shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="employer-backfill-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-[#E2E8F0] px-4 py-4">
          <h2 id="employer-backfill-title" className="text-lg font-semibold text-[#1E293B]">
            We upgraded Career Risk
          </h2>
          <p className="mt-2 text-sm text-[#64748B]">
            Confirm your employer to see live financial health data in your Career Risk score.
            Takes 10 seconds — or skip and we&apos;ll keep using your assessment answers.
          </p>
        </div>

        <div className="flex flex-col gap-4 overflow-y-auto px-4 py-4">
          {loading ? (
            <p className="text-sm text-[#64748B]">Loading…</p>
          ) : (
            <>
              <div>
                <label className={labelClass} htmlFor="backfill-employer">Employer</label>
                <EmployerSelect
                  id="backfill-employer"
                  value={employer}
                  onChange={setEmployer}
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="backfill-employer-type">
                  Which best describes your employer?
                </label>
                <select
                  id="backfill-employer-type"
                  className={inputClass}
                  value={employerType}
                  onChange={(e) => setEmployerType(e.target.value as EmployerType | '')}
                >
                  <option value="">Select…</option>
                  {EMPLOYER_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {helper ? (
                  <p className="mt-1.5 text-sm text-[#64748B]">{helper}</p>
                ) : null}
              </div>
              {error ? (
                <p className="text-sm text-red-600" role="alert">{error}</p>
              ) : null}
            </>
          )}
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-[#E2E8F0] px-4 py-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={handleDismiss}
            className="min-h-11 rounded-lg px-4 text-sm text-[#64748B] hover:text-[#1E293B]"
          >
            Skip for now
          </button>
          <button
            type="button"
            disabled={saving || loading}
            onClick={() => void handleSave()}
            className="min-h-11 rounded-xl bg-[#5B2D8E] px-6 font-semibold text-white hover:opacity-95 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
