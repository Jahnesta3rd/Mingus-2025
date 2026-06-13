import React, { useCallback, useEffect, useState } from 'react';
import { csrfHeaders } from '../utils/csrfHeaders';

interface RepairItem {
  name: string;
  cost: number;
  frequency_note: string;
  likelihood_pct: number;
}

interface CarSuggestion {
  name: string;
  price_range: string;
  reason: string;
}

export interface VinAdvisorData {
  vin: string;
  year: number;
  make: string;
  model: string;
  book_value: number;
  vehicle_age: number;
  annual_repair_exposure: number;
  repair_to_value_ratio: number;
  verdict: 'keep' | 'monitor' | 'replace';
  replacement_year_range: { from: number; to: number };
  top_repairs: RepairItem[];
  car_suggestions: CarSuggestion[];
  annual_salary: number;
}

interface VinAdvisorApiResponse {
  status?: string;
  data?: VinAdvisorData;
  error?: string;
  message?: string;
}

export interface VinAdvisorProps {
  userId: number;
  className?: string;
}

function likelihoodBarColor(pct: number): string {
  if (pct < 50) return 'bg-green-400';
  if (pct <= 70) return 'bg-amber-400';
  return 'bg-red-400';
}

function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div className={`flex flex-col gap-3 ${className ?? ''}`}>
      <div className="h-6 w-3/4 rounded bg-gray-200 animate-pulse" />
      <div className="h-6 w-full rounded bg-gray-200 animate-pulse" />
      <div className="h-6 w-1/2 rounded bg-gray-200 animate-pulse" />
    </div>
  );
}

export default function VinAdvisor({ userId, className }: VinAdvisorProps) {
  const [data, setData] = useState<VinAdvisorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<'no_vehicle' | 'fetch_error' | null>(null);
  const [fetchKey, setFetchKey] = useState(0);

  const loadAdvisor = useCallback(async (signal: AbortSignal) => {
    if (!userId || userId <= 0) {
      setLoading(false);
      setData(null);
      setError('fetch_error');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/vin-advisor/${userId}`, {
        credentials: 'include',
        headers: csrfHeaders(),
        signal,
      });

      if (res.status === 404) {
        setData(null);
        setError('no_vehicle');
        return;
      }

      if (!res.ok) {
        setData(null);
        setError('fetch_error');
        return;
      }

      const body = (await res.json()) as VinAdvisorApiResponse;
      if (body.status === 'ok' && body.data) {
        setData(body.data);
        setError(null);
      } else {
        setData(null);
        setError('fetch_error');
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return;
      }
      setData(null);
      setError('fetch_error');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    const controller = new AbortController();
    void loadAdvisor(controller.signal);
    return () => controller.abort();
  }, [loadAdvisor, fetchKey]);

  const handleRetry = () => {
    setFetchKey((k) => k + 1);
  };

  if (loading) {
    return <LoadingSkeleton className={className} />;
  }

  if (error === 'no_vehicle') {
    return (
      <div className={`flex flex-col items-center py-10 text-center ${className ?? ''}`}>
        <svg
          className="mb-3 h-10 w-10 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10m10 0H3m10 0h2l3 4h3a1 1 0 011 1v2H13v-7z"
          />
        </svg>
        <h3 className="text-base font-semibold text-gray-900">No vehicle on file</h3>
        <p className="mt-1 text-sm text-gray-500">
          Add your vehicle in Settings to see your advisor.
        </p>
      </div>
    );
  }

  if (error === 'fetch_error' || !data) {
    return (
      <div className={`rounded-xl bg-white p-6 text-center shadow-sm ${className ?? ''}`}>
        <p className="text-sm text-gray-600">
          Unable to load vehicle advisor. Please try again.
        </p>
        <button
          type="button"
          onClick={handleRetry}
          className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          Retry
        </button>
      </div>
    );
  }

  const ageLabel = data.vehicle_age === 1 ? '1 yr' : `${data.vehicle_age} yrs`;

  return (
    <div className={className}>
      <div className="mb-6 flex flex-wrap gap-3">
        <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
          {data.year} {data.make} {data.model}
        </span>
        <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
          Book value: ${data.book_value.toLocaleString()}
        </span>
        <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
          Age: {ageLabel}
        </span>
      </div>

      <div className="mb-4 rounded-xl bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-base font-semibold text-gray-900">
          Top 3 repair risks — {data.year} {data.make}
        </h3>
        <table className="w-full">
          <thead>
            <tr>
              <th className="w-1/2 border-b border-gray-200 pb-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Repair
              </th>
              <th className="w-1/4 border-b border-gray-200 pb-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Likelihood
              </th>
              <th className="w-1/4 border-b border-gray-200 pb-2 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Est. cost
              </th>
            </tr>
          </thead>
          <tbody>
            {data.top_repairs.map((repair) => (
              <tr key={repair.name} className="border-b border-gray-100 last:border-0">
                <td className="py-3 pr-4 align-top">
                  <div className="text-sm font-medium text-gray-900">{repair.name}</div>
                  <div className="mt-0.5 text-xs text-gray-500">{repair.frequency_note}</div>
                </td>
                <td className="py-3 pr-4 align-top">
                  <div className="h-2 w-full rounded-full bg-gray-100">
                    <div
                      className={`h-2 rounded-full ${likelihoodBarColor(repair.likelihood_pct)}`}
                      style={{ width: `${Math.min(repair.likelihood_pct, 100)}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    {repair.likelihood_pct}% likely
                  </div>
                </td>
                <td className="py-3 text-right align-top text-sm font-semibold text-gray-900">
                  ${repair.cost.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-4 border-t border-gray-100 pt-4 text-sm text-gray-600">
          Estimated annual exposure:{' '}
          <span className="font-semibold text-gray-900">
            ${data.annual_repair_exposure.toLocaleString()}
          </span>{' '}
          (40% of top-3 scenario cost)
        </p>
      </div>

      {data.verdict === 'keep' && (
        <div className="mb-4 rounded-xl border-2 border-green-300 bg-green-50 p-6">
          <div className="flex items-start gap-3">
            <svg
              viewBox="0 0 20 20"
              fill="currentColor"
              className="mt-0.5 h-5 w-5 shrink-0 text-green-500"
              aria-hidden
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="text-sm font-semibold text-green-800">Keep your car</p>
              <p className="mt-1 text-sm text-green-700">
                Repair exposure (${data.annual_repair_exposure.toLocaleString()}/yr) is well below
                book value. Recommended replacement window: {data.replacement_year_range.from}–
                {data.replacement_year_range.to}.
              </p>
            </div>
          </div>
        </div>
      )}

      {data.verdict === 'monitor' && (
        <div className="mb-4 rounded-xl border-2 border-amber-300 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <svg
              viewBox="0 0 20 20"
              fill="currentColor"
              className="mt-0.5 h-5 w-5 shrink-0 text-amber-500"
              aria-hidden
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="text-sm font-semibold text-amber-800">Monitor closely</p>
              <p className="mt-1 text-sm text-amber-700">
                Weigh each repair against book value (${data.book_value.toLocaleString()}). If any
                single repair exceeds ${Math.round(data.book_value * 0.2).toLocaleString()},
                consider replacing.
              </p>
            </div>
          </div>
        </div>
      )}

      {data.verdict === 'replace' && (
        <div className="mb-4 rounded-xl border-2 border-red-300 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <svg
              viewBox="0 0 20 20"
              fill="currentColor"
              className="mt-0.5 h-5 w-5 shrink-0 text-red-500"
              aria-hidden
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="text-sm font-semibold text-red-800">Time to replace</p>
              <p className="mt-1 text-sm text-red-700">
                Annual repair exposure exceeds 50% of book value or your vehicle is over 12 years
                old.
              </p>
            </div>
          </div>
        </div>
      )}

      {data.annual_salary > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Suggested replacements — based on your income
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {data.car_suggestions.map((car) => (
              <div key={car.name} className="rounded-lg border border-gray-200 p-4">
                <div className="text-sm font-semibold text-gray-900">{car.name}</div>
                <span className="mt-1 inline-block rounded bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                  {car.price_range}
                </span>
                <p className="mt-2 text-xs leading-relaxed text-gray-500">{car.reason}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-gray-400">
            Budget estimate: 25% of annual salary or 2.5× current book value, whichever is lower.
          </p>
        </div>
      )}
    </div>
  );
}
