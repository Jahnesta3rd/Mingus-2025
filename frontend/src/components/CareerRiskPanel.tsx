import React from 'react';
import type { CareerRiskData } from '../types/snapshot';

interface CareerRiskPanelProps {
  data: CareerRiskData | null;
  loading?: boolean;
  onOpenEmployerBackfill?: () => void;
}

function formatPct(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso + (iso.includes('T') ? '' : 'T00:00:00')).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

export default function CareerRiskPanel({
  data,
  loading = false,
  onOpenEmployerBackfill,
}: CareerRiskPanelProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <p className="text-sm text-[#64748B]">Loading career risk…</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-[#1E293B]">Career Risk</h3>
        <p className="mt-2 text-sm text-[#64748B]">
          Complete your career profile and layoff risk assessment to see your 12-month separation probability.
        </p>
      </div>
    );
  }

  const employerName = data.employer_name?.trim() || 'Your employer';

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-[#1E293B]">Career Risk</h3>
      <p className="mt-1 text-3xl font-bold tabular-nums text-[#1E293B]">
        {formatPct(data.probability_12mo)}
      </p>
      <p className="text-sm text-[#64748B]">Estimated 12-month job separation probability</p>

      <div className="mt-4 grid gap-2 text-sm text-[#1E293B] sm:grid-cols-3">
        <div className="rounded-lg bg-[#F8FAFC] px-3 py-2">
          <span className="text-xs text-[#64748B]">Market</span>
          <p className="font-medium tabular-nums">×{data.market_multiplier.toFixed(2)}</p>
        </div>
        <div className="rounded-lg bg-[#F8FAFC] px-3 py-2">
          <span className="text-xs text-[#64748B]">Occupation</span>
          <p className="font-medium tabular-nums">×{data.occupation_multiplier.toFixed(2)}</p>
        </div>
        <div className="rounded-lg bg-[#F8FAFC] px-3 py-2">
          <span className="text-xs text-[#64748B]">Employer</span>
          <p className="font-medium tabular-nums">×{data.employer_multiplier.toFixed(2)}</p>
        </div>
      </div>

      <div className="mt-6 border-t border-[#E2E8F0] pt-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-[#64748B]">
          Methodology
        </h4>
        <div className="mt-2 text-sm text-[#1E293B]">
          {data.data_source === 'sec_edgar' ? (
            <>
              <p>
                Employer signal: {employerName}&apos;s last 4 quarters of public financials, filed
                with the SEC. Health score: {data.employer_health_score ?? '—'}/100.
              </p>
              {data.employer_health_components ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {(
                    [
                      ['Revenue', data.employer_health_components.revenue_delta],
                      ['Margin', data.employer_health_components.margin],
                      ['FCF', data.employer_health_components.fcf],
                      ['Runway', data.employer_health_components.runway],
                      ['Leverage', data.employer_health_components.leverage],
                    ] as const
                  ).map(([label, score]) => (
                    <span
                      key={label}
                      className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-700"
                    >
                      {label} {score > 0 ? `+${score}` : score}
                    </span>
                  ))}
                </div>
              ) : null}
            </>
          ) : null}

          {data.data_source === '8k_filing' ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
              {employerName} filed an 8-K disclosing layoffs on{' '}
              {data.employer_layoff_event
                ? formatDate(data.employer_layoff_event.filing_date)
                : '—'}
              . This override expires{' '}
              {data.employer_layoff_event
                ? formatDate(data.employer_layoff_event.expires_at)
                : '—'}.
            </div>
          ) : null}

          {data.data_source === 'user_reported' ? (
            <p>Employer signal: your last Layoff Risk Assessment answers.</p>
          ) : null}

          {data.data_source === 'unresolved' ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
              <p>
                We couldn&apos;t match your employer to a public company. Update your profile to
                enable live employer health data.
              </p>
              {onOpenEmployerBackfill ? (
                <button
                  type="button"
                  onClick={onOpenEmployerBackfill}
                  className="mt-2 text-sm font-semibold text-[#5B2D8E] hover:underline"
                >
                  Update employer
                </button>
              ) : null}
            </div>
          ) : null}

          {data.data_source === 'unsupported' ? (
            <p>
              Employer signal: live data not yet available for your employer type. Using your
              assessment answers.
            </p>
          ) : null}

          {data.data_source === undefined ? (
            <p>Employer signal: your last Layoff Risk Assessment answers.</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
