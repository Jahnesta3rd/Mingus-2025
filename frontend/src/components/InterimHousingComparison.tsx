import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, Home, Loader2, Users } from 'lucide-react';
import {
  getInterimHousingScenarios,
  type InterimHousingConversationTemplate,
  type InterimHousingScenario,
  type InterimHousingScenariosResponse,
} from '../api/interimHousingAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface InterimHousingComparisonProps {
  zipCode?: string;
  monthlyGap?: number;
  startupCostNeeded?: number;
  className?: string;
}

const SCENARIO_ICONS: Record<string, React.ReactNode> = {
  roommate: <Users className="h-5 w-5 text-blue-600" />,
  family: <Home className="h-5 w-5 text-green-600" />,
  sublet: <Home className="h-5 w-5 text-purple-600" />,
};

const FEATURE_LABELS: Record<string, string> = {
  privacy: 'Privacy',
  lease_flexibility: 'Lease flexibility',
  furniture_included: 'Furniture included',
  furnished: 'Furnished',
  month_to_month: 'Month-to-month',
  social_support: 'Social support',
  burnout_risk: 'Burnout risk',
};

function difficultyClass(level: string): string {
  if (level === 'easy') return 'bg-green-100 text-green-800';
  if (level === 'hard') return 'bg-red-100 text-red-800';
  return 'bg-yellow-100 text-yellow-800';
}

function formatFeatureValue(value: string | boolean): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function ConversationPanel({
  templateKey,
  template,
}: {
  templateKey: string;
  template: InterimHousingConversationTemplate;
}) {
  const [open, setOpen] = useState(false);
  const title =
    templateKey === 'how_to_ask_family'
      ? 'How to ask family'
      : templateKey === 'how_to_vet_roommate'
        ? 'How to vet roommate'
        : 'Sublet red flags';

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-medium text-gray-900">{title}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        )}
      </button>
      {open ? (
        <div className="space-y-3 border-t border-gray-100 px-4 py-3 text-sm text-gray-700">
          <p>{template.summary}</p>
          {template.sample_opener ? (
            <blockquote className="rounded-md bg-gray-50 p-3 italic text-gray-600">
              {template.sample_opener}
            </blockquote>
          ) : null}
          {template.talking_points?.length ? (
            <ul className="list-disc space-y-1 pl-5">
              {template.talking_points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          ) : null}
          {template.checklist?.length ? (
            <ul className="list-disc space-y-1 pl-5">
              {template.checklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          {template.red_flags?.length ? (
            <div>
              <p className="mb-1 font-medium text-red-700">Red flags</p>
              <ul className="list-disc space-y-1 pl-5 text-red-700">
                {template.red_flags.map((flag) => (
                  <li key={flag}>{flag}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {template.must_haves?.length ? (
            <div>
              <p className="mb-1 font-medium text-green-700">Must-haves</p>
              <ul className="list-disc space-y-1 pl-5 text-green-700">
                {template.must_haves.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function ScenarioCard({
  scenario,
  soloTimeline,
}: {
  scenario: InterimHousingScenario;
  soloTimeline: number | null;
}) {
  const monthsSaved =
    soloTimeline != null && scenario.timeline_months != null
      ? Math.max(0, soloTimeline - scenario.timeline_months)
      : null;

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          {SCENARIO_ICONS[scenario.key]}
          <h3 className="font-semibold text-gray-900">{scenario.name}</h3>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${difficultyClass(
            scenario.difficulty,
          )}`}
        >
          {scenario.difficulty}
        </span>
      </div>

      <dl className="mb-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-gray-500">Monthly</dt>
          <dd className="font-semibold text-gray-900">
            {scenario.monthly_rent_range
              ? `${formatCurrency(scenario.monthly_rent_range.min)}–${formatCurrency(
                  scenario.monthly_rent_range.max,
                )}`
              : formatCurrency(scenario.monthly_rent)}
          </dd>
        </div>
        <div>
          <dt className="text-gray-500">Startup</dt>
          <dd className="font-semibold text-gray-900">
            {formatCurrency(scenario.startup_cost)}
          </dd>
        </div>
        <div>
          <dt className="text-gray-500">Monthly savings</dt>
          <dd className="font-semibold text-green-700">
            {formatCurrency(scenario.monthly_savings_vs_solo)}/mo
          </dd>
        </div>
        <div>
          <dt className="text-gray-500">Timeline</dt>
          <dd className="font-semibold text-gray-900">
            {scenario.timeline_months != null ? `${scenario.timeline_months} mo` : '—'}
            {monthsSaved != null && monthsSaved > 0 ? (
              <span className="ml-1 text-xs text-green-600">({monthsSaved} mo faster)</span>
            ) : null}
          </dd>
        </div>
      </dl>

      <div className="mb-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-green-700">Pros</p>
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
            {scenario.pros.map((pro) => (
              <li key={pro}>{pro}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-red-700">Cons</p>
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
            {scenario.cons.map((con) => (
              <li key={con}>{con}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

function FeatureMatrix({ data }: { data: InterimHousingScenariosResponse }) {
  const keys = data.feature_matrix_keys;
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500">
          <tr>
            <th className="px-3 py-2">Feature</th>
            {data.scenarios.map((scenario) => (
              <th key={scenario.key} className="px-3 py-2">
                {scenario.key === 'roommate' ? 'Roommate' : scenario.key === 'family' ? 'Family' : 'Sublet'}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key} className="border-t border-gray-100">
              <td className="px-3 py-2 font-medium text-gray-700">
                {FEATURE_LABELS[key] ?? key}
              </td>
              {data.scenarios.map((scenario) => (
                <td key={`${scenario.key}-${key}`} className="px-3 py-2 text-gray-600">
                  {formatFeatureValue(scenario.features[key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PhasedTimeline({ data }: { data: InterimHousingScenariosResponse }) {
  const { phased_exit_plan: plan } = data;
  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
      <h3 className="mb-1 font-semibold text-gray-900">Phased exit plan</h3>
      <p className="mb-4 text-sm text-gray-600">{plan.summary}</p>
      <ol className="space-y-3">
        {plan.phases.map((phase) => (
          <li key={phase.phase} className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              {phase.phase}
            </span>
            <div>
              <p className="font-medium text-gray-900">{phase.label}</p>
              <p className="text-sm text-gray-600">
                {phase.duration_months} months
                {phase.monthly_savings != null
                  ? ` · saves ${formatCurrency(phase.monthly_savings)}/mo`
                  : ''}
                {phase.cumulative_savings != null
                  ? ` · ${formatCurrency(phase.cumulative_savings)} banked`
                  : ''}
                {phase.remaining_startup_target != null
                  ? ` · ${formatCurrency(phase.remaining_startup_target)} still needed`
                  : ''}
              </p>
              <p className="text-xs text-gray-500">{phase.goal}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-4 text-sm font-medium text-gray-900">
        Total to solo readiness: {plan.total_months_to_solo_readiness} months
        {plan.months_saved_vs_solo != null && plan.months_saved_vs_solo > 0 ? (
          <span className="ml-2 text-green-700">
            ({plan.months_saved_vs_solo} months faster than solo path)
          </span>
        ) : null}
      </p>
    </div>
  );
}

export default function InterimHousingComparison({
  zipCode,
  monthlyGap,
  startupCostNeeded,
  className = '',
}: InterimHousingComparisonProps) {
  const { getAccessToken } = useAuth();
  const [data, setData] = useState<InterimHousingScenariosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getInterimHousingScenarios(
        {
          zipCode,
          monthlyGap,
          startupCostNeeded,
        },
        { getAccessToken },
      );
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load housing scenarios');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, monthlyGap, startupCostNeeded, zipCode]);

  useEffect(() => {
    void load();
  }, [load]);

  const solo = data?.solo_comparison;
  const templateEntries = useMemo(() => {
    if (!data?.conversation_templates) return [];
    return Object.entries(data.conversation_templates);
  }, [data]);

  if (loading) {
    return (
      <section
        className={`flex items-center justify-center rounded-xl border border-gray-200 bg-white p-8 ${className}`}
      >
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className={`rounded-xl border border-red-200 bg-red-50 p-4 ${className}`}>
        <p className="text-sm text-red-700">{error ?? 'Unable to load interim housing options.'}</p>
      </section>
    );
  }

  return (
    <section className={`rounded-xl border border-gray-200 bg-gray-50 p-4 sm:p-6 ${className}`}>
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Interim housing options</h2>
        <p className="text-sm text-gray-600">
          Roommate, family, and sublet paths compared to a solo apartment in{' '}
          {data.zip_code} (2BR market ~{formatCurrency(data.market_rent_2br)}/mo).
        </p>
      </header>

      {solo ? (
        <div className="mb-5 rounded-lg border border-orange-200 bg-orange-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-orange-800">
            Compare with solo (ICC)
          </p>
          <div className="mt-2 flex flex-wrap gap-4 text-sm">
            <span>
              <strong>{formatCurrency(solo.monthly_rent)}</strong>/mo rent
            </span>
            <span>
              Gap <strong>{formatCurrency(solo.monthly_gap)}</strong>/mo
            </span>
            <span>
              Startup <strong>{formatCurrency(solo.startup_cost_needed)}</strong>
            </span>
            <span>
              Timeline{' '}
              <strong>
                {solo.timeline_months != null ? `${solo.timeline_months} months` : '—'}
              </strong>
            </span>
          </div>
        </div>
      ) : null}

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        {data.scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.key}
            scenario={scenario}
            soloTimeline={solo?.timeline_months ?? null}
          />
        ))}
      </div>

      <div className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Feature comparison</h3>
        <FeatureMatrix data={data} />
      </div>

      <div className="mb-6">
        <PhasedTimeline data={data} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Conversation templates</h3>
        <div className="space-y-2">
          {templateEntries.map(([key, template]) => (
            <ConversationPanel key={key} templateKey={key} template={template} />
          ))}
        </div>
      </div>
    </section>
  );
}
