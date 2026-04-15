import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useBugReport } from '../hooks/useBugReport';

const SUBMIT_PURPLE = '#5B2D8E';

export default function BugReportButton() {
  const {
    isOpen,
    phase,
    ticketNumber,
    description,
    setDescription,
    error,
    openModal,
    closeModal,
    submitReport,
  } = useBugReport();

  const [entered, setEntered] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setEntered(false);
      return;
    }
    const id = requestAnimationFrame(() => setEntered(true));
    return () => cancelAnimationFrame(id);
  }, [isOpen]);

  const modal =
    isOpen &&
    createPortal(
      <>
        <div
          role="presentation"
          className="fixed inset-0 z-50 bg-black/40"
          onClick={() => {
            if (phase !== 'submitting') closeModal();
          }}
        />
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="bug-report-title"
          className={[
            'fixed z-50 bg-white p-6 shadow-xl duration-300 ease-out',
            'bottom-0 left-0 right-0 rounded-t-2xl transition-[transform,opacity]',
            'max-sm:translate-x-0',
            entered ? 'max-sm:translate-y-0 max-sm:opacity-100' : 'max-sm:translate-y-full max-sm:opacity-0',
            'sm:bottom-auto sm:left-1/2 sm:top-1/2 sm:right-auto sm:max-w-md sm:w-[calc(100%-2rem)] sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-2xl sm:transition-opacity',
            entered ? 'sm:opacity-100' : 'sm:opacity-0',
          ].join(' ')}
        >
          <div className="mb-4 flex items-start justify-between gap-3">
            <h2 id="bug-report-title" className="text-[18px] font-bold text-gray-900">
              Report a Bug
            </h2>
            <button
              type="button"
              onClick={closeModal}
              disabled={phase === 'submitting'}
              className="rounded-lg p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-800 disabled:pointer-events-none disabled:opacity-40"
              aria-label="Close"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
                <path
                  d="M5 5l10 10M15 5L5 15"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>

          {phase === 'success' ? (
            <>
              <div className="flex justify-center">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden>
                  <circle cx="32" cy="32" r="30" stroke="#22c55e" strokeWidth="3" fill="none" />
                  <path
                    d="M18 33l10 10 18-22"
                    stroke="#22c55e"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                  />
                </svg>
              </div>
              <p className="mt-4 text-center text-[20px] font-bold text-gray-900">Report received</p>
              <p className="mt-2 text-center text-[13px] text-gray-500">Your ticket number:</p>
              <div className="mx-auto mt-2 max-w-xs rounded-xl bg-purple-100 px-4 py-3 text-center">
                <span className="text-[24px] font-bold" style={{ color: SUBMIT_PURPLE }}>
                  {ticketNumber ?? '—'}
                </span>
              </div>
              <p className="mt-3 text-center text-[13px] text-gray-500">
                We&apos;ve emailed your ticket number to you. Reply to that email to add more details or follow
                up.
              </p>
              <button
                type="button"
                onClick={closeModal}
                className="mt-6 w-full rounded-xl border border-gray-300 bg-white py-3 font-medium text-gray-900 hover:bg-gray-50"
              >
                Done
              </button>
            </>
          ) : (
            <>
              <p className="mb-4 text-sm text-gray-600">
                Describe what happened. We&apos;ll get your ticket number back to you right away.
              </p>

              {phase === 'error' && error && (
                <div className="mb-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  {error}
                </div>
              )}

              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value.slice(0, 1000))}
                placeholder="What went wrong? Be as specific as you can..."
                rows={4}
                maxLength={1000}
                disabled={phase === 'submitting'}
                className="w-full resize-none rounded-xl border border-gray-300 p-3 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 disabled:bg-gray-100"
              />
              <p className="mt-1 text-right text-[11px] text-gray-500">{description.length}/1000</p>
              <p className="mt-1 text-[11px] text-gray-500">
                We&apos;ll automatically attach your account context.
              </p>

              {phase === 'submitting' ? (
                <button
                  type="button"
                  disabled
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gray-300 py-3 font-medium text-gray-600"
                >
                  <span
                    className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-gray-700"
                    aria-hidden
                  />
                  Sending...
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void submitReport()}
                  disabled={description.trim().length < 10}
                  className="mt-4 w-full rounded-xl py-3 font-semibold text-white transition-colors disabled:bg-gray-300 disabled:text-gray-500"
                  style={
                    description.trim().length >= 10
                      ? { backgroundColor: SUBMIT_PURPLE }
                      : { backgroundColor: undefined }
                  }
                >
                  Submit Report
                </button>
              )}
            </>
          )}
        </div>
      </>,
      document.body,
    );

  return (
    <>
      <button
        type="button"
        onClick={openModal}
        title="Report a bug"
        aria-label="Report a bug"
        className="rounded-lg p-2 text-gray-400 hover:text-purple-600"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
          <path
            d="M2 3a1 1 0 011-1h14a1 1 0 011 1v10a1 1 0 01-1 1H6l-4 3V3z"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <text x="10" y="11" textAnchor="middle" fontSize="8" fontWeight="bold" fill="currentColor">
            !
          </text>
        </svg>
      </button>
      {modal}
    </>
  );
}
