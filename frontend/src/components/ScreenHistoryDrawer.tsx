import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import type { CompanyScreen } from '../types/companyScreen';

interface ScreenHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectScreen: (screen: CompanyScreen) => void;
  authToken: string;
}

function relativeDate(iso: string): string {
  try {
    const then = new Date(iso).getTime();
    const now = Date.now();
    const diffDays = Math.floor((now - then) / 86400000);
    if (diffDays <= 0) return 'today';
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
  } catch {
    return iso;
  }
}

function isExpiringSoon(expiresAt: string): boolean {
  try {
    const expires = new Date(expiresAt).getTime();
    const threeDays = 3 * 86400000;
    return expires - Date.now() <= threeDays;
  } catch {
    return false;
  }
}

function compositeBandClasses(
  band: CompanyScreen['composite_band'],
): string {
  switch (band) {
    case 'strong':
      return 'bg-green-100 text-green-800';
    case 'mixed':
      return 'bg-yellow-100 text-yellow-800';
    case 'caution':
      return 'bg-orange-100 text-orange-800';
    case 'high_risk':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-500';
  }
}

export default function ScreenHistoryDrawer({
  isOpen,
  onClose,
  onSelectScreen,
  authToken,
}: ScreenHistoryDrawerProps) {
  const [screens, setScreens] = useState<CompanyScreen[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchHistory = () => {
    setLoading(true);
    setError(false);
    fetch('/api/company-screen/history', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    })
      .then(async (resp) => {
        if (!resp.ok) throw new Error('fetch failed');
        const data = await resp.json();
        setScreens(Array.isArray(data.screens) ? data.screens : []);
      })
      .catch(() => {
        setError(true);
        setScreens([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen, authToken]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/30"
        role="presentation"
        onClick={onClose}
      />
      <aside
        className="fixed right-0 top-0 z-50 flex h-full w-96 max-w-full translate-x-0 flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out"
        aria-label="Past screens"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white px-4 py-4">
          <h2 className="text-base font-semibold text-[#1E293B]">Past Screens</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
            aria-label="Close drawer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {loading ? (
            <div className="space-y-3">
              <div className="h-12 animate-pulse rounded bg-gray-200" />
              <div className="h-12 w-4/5 animate-pulse rounded bg-gray-200" />
              <div className="h-12 w-3/5 animate-pulse rounded bg-gray-200" />
            </div>
          ) : null}

          {!loading && error ? (
            <div className="py-8 text-center">
              <p className="text-sm text-[#1E293B]">Couldn&apos;t load past screens.</p>
              <button
                type="button"
                onClick={fetchHistory}
                className="mt-2 text-sm font-medium text-purple-700 underline hover:text-purple-900"
              >
                Retry
              </button>
            </div>
          ) : null}

          {!loading && !error && screens.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-[#1E293B]">No screens yet.</p>
              <p className="mt-1 text-sm text-gray-500">
                Screen a company before your next interview.
              </p>
            </div>
          ) : null}

          {!loading && !error && screens.length > 0 ? (
            <ul className="space-y-2">
              {screens.map((screen) => (
                <li key={screen.id}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectScreen(screen);
                      onClose();
                    }}
                    className="w-full cursor-pointer rounded-lg px-3 py-3 text-left hover:bg-gray-50"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium text-[#1E293B]">
                        {screen.employer_name}
                      </span>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-xs capitalize ${compositeBandClasses(
                          screen.composite_band,
                        )}`}
                      >
                        {screen.composite_band?.replace('_', ' ') ?? '—'}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">
                      Screened {relativeDate(screen.created_at)}
                    </p>
                    {isExpiringSoon(screen.expires_at) ? (
                      <span className="mt-2 inline-flex rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                        Refreshing soon
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </aside>
    </>
  );
}
