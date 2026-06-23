import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';
import EmployerSelect, { type EmployerSelectValue } from './EmployerSelect';
import type { CompanyScreen } from '../types/companyScreen';

interface CompanyScreenEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScreenComplete: (screen: CompanyScreen) => void;
  authToken: string;
  prefilledEmployerName?: string;
  prefilledEmployerCik?: string;
}

const LOADING_STEPS = [
  'Checking financial health...',
  'Analyzing company language...',
  'Reading community signals...',
] as const;

function formatResetsOn(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}

export default function CompanyScreenEntryModal({
  isOpen,
  onClose,
  onScreenComplete,
  authToken,
  prefilledEmployerName,
  prefilledEmployerCik,
}: CompanyScreenEntryModalProps) {
  const navigate = useNavigate();
  const cancelledRef = useRef(false);
  const [employerName, setEmployerName] = useState(prefilledEmployerName ?? '');
  const [employerCik, setEmployerCik] = useState<string | null>(
    prefilledEmployerCik ?? null,
  );
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [tierGateMessage, setTierGateMessage] = useState<string | null>(null);
  const [screenLimitMessage, setScreenLimitMessage] = useState<string | null>(null);
  const [screenLimitResetsOn, setScreenLimitResetsOn] = useState<string | null>(null);
  const [genericError, setGenericError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setEmployerName(prefilledEmployerName ?? '');
    setEmployerCik(prefilledEmployerCik ?? null);
    setTierGateMessage(null);
    setScreenLimitMessage(null);
    setScreenLimitResetsOn(null);
    setGenericError(null);
    setLoading(false);
    setLoadingStep(0);
    cancelledRef.current = false;
  }, [isOpen, prefilledEmployerName, prefilledEmployerCik]);

  useEffect(() => {
    if (!loading) return;
    if (loadingStep === 0) {
      const timer = window.setTimeout(() => setLoadingStep(1), 2500);
      return () => window.clearTimeout(timer);
    }
    if (loadingStep === 1) {
      const timer = window.setTimeout(() => setLoadingStep(2), 5000);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [loading, loadingStep]);

  const handleEmployerChange = (val: EmployerSelectValue) => {
    setEmployerName(val.name);
    setEmployerCik(val.cik);
  };

  const handleCancel = () => {
    cancelledRef.current = true;
    setLoading(false);
    setLoadingStep(0);
  };

  const runScreen = useCallback(async () => {
    cancelledRef.current = false;
    setLoading(true);
    setLoadingStep(0);
    setTierGateMessage(null);
    setScreenLimitMessage(null);
    setScreenLimitResetsOn(null);
    setGenericError(null);

    try {
      const resp = await fetch('/api/company-screen/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          employer_name: employerName.trim(),
          employer_cik: employerCik || null,
        }),
      });

      const data = await resp.json().catch(() => ({}));

      if (resp.status === 403 && data.error === 'TIER_GATE') {
        setLoading(false);
        setLoadingStep(0);
        setTierGateMessage(
          'Company Screen is available on Career Pro and above.',
        );
        return;
      }

      if (resp.status === 429 && data.error === 'SCREEN_LIMIT') {
        setLoading(false);
        setLoadingStep(0);
        setScreenLimitMessage("You've used all 10 screens this month.");
        setScreenLimitResetsOn(
          typeof data.resets_on === 'string' ? data.resets_on : null,
        );
        return;
      }

      if (!resp.ok) {
        setLoading(false);
        setLoadingStep(0);
        setGenericError(
          typeof data.message === 'string'
            ? data.message
            : 'Something went wrong. Please try again.',
        );
        return;
      }

      if (cancelledRef.current) {
        setLoading(false);
        setLoadingStep(0);
        return;
      }

      setLoading(false);
      setLoadingStep(0);
      onScreenComplete(data as CompanyScreen);
    } catch {
      if (!cancelledRef.current) {
        setLoading(false);
        setLoadingStep(0);
        setGenericError('Something went wrong. Please try again.');
      }
    }
  }, [authToken, employerCik, employerName, onScreenComplete]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="company-screen-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 rounded p-1 text-gray-500 hover:bg-gray-100"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6 pt-10">
          <h2
            id="company-screen-modal-title"
            className="text-lg font-bold text-[#1E293B]"
          >
            Screen This Company
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Get a financial health, culture, and community brief before your
            interview.
          </p>

          {tierGateMessage ? (
            <div className="mt-4 rounded-lg border border-purple-200 bg-purple-50 p-4">
              <p className="text-sm text-[#1E293B]">{tierGateMessage}</p>
              <button
                type="button"
                onClick={() => navigate('/settings/billing')}
                className="mt-3 w-full rounded-lg bg-purple-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-purple-800"
              >
                Upgrade to Career Pro
              </button>
            </div>
          ) : null}

          {screenLimitMessage ? (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm text-[#1E293B]">{screenLimitMessage}</p>
              {screenLimitResetsOn ? (
                <p className="mt-1 text-sm text-gray-600">
                  Resets on {formatResetsOn(screenLimitResetsOn)}
                </p>
              ) : null}
            </div>
          ) : null}

          {genericError ? (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm text-red-800">{genericError}</p>
            </div>
          ) : null}

          {loading ? (
            <div className="mt-6">
              <div className="flex items-center gap-3">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-purple-700" />
                <p className="text-sm text-[#1E293B]">
                  {LOADING_STEPS[loadingStep]}
                </p>
              </div>
              <button
                type="button"
                onClick={handleCancel}
                className="mt-4 text-sm text-gray-500 underline hover:text-gray-700"
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              {!tierGateMessage && !screenLimitMessage ? (
                <div className="mt-4">
                  <label
                    htmlFor="company-screen-employer"
                    className="mb-1.5 block text-sm font-medium text-[#1E293B]"
                  >
                    Employer
                  </label>
                  <EmployerSelect
                    id="company-screen-employer"
                    value={{ cik: employerCik, name: employerName }}
                    onChange={handleEmployerChange}
                    disabled={loading}
                  />
                </div>
              ) : null}

              {!tierGateMessage && !screenLimitMessage ? (
                <button
                  type="button"
                  disabled={employerName.trim() === ''}
                  onClick={runScreen}
                  className="mt-6 w-full rounded-lg bg-purple-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-purple-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Run Screen
                </button>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
