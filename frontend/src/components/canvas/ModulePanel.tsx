import { useCallback, useState, type ReactElement } from 'react';
import type {
  CommitFieldResponse,
  CommitModuleResponse,
  ExpenseCategoryId,
  ModuleData,
  ModuleId,
  ModuleState,
} from '../../types/modularOnboarding';
import {
  EXPENSE_CATEGORY_IDS,
  MAX_VEHICLE_YEAR,
  MIN_VEHICLE_YEAR,
} from '../../types/modularOnboarding';
import { ChipField } from './ChipField';

const YES_NO_CHIPS = [
  { value: 'true', label: 'Yes' },
  { value: 'false', label: 'No' },
] as const;

const PAY_FREQUENCY_CHIPS = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Biweekly' },
  { value: 'semimonthly', label: 'Semimonthly' },
  { value: 'monthly', label: 'Monthly' },
] as const;

const HOUSING_TYPE_CHIPS = [
  { value: 'rent', label: 'Rent' },
  { value: 'own', label: 'Own' },
] as const;

const VEHICLE_COUNT_CHIPS = [
  { value: '0', label: 'None' },
  { value: '1', label: '1' },
  { value: '2', label: '2' },
  { value: '3', label: '3+' },
] as const;

const RELATIONSHIP_CHIPS = [
  { value: 'single', label: 'Single' },
  { value: 'dating', label: 'Dating' },
  { value: 'partnered', label: 'Partnered' },
  { value: 'married', label: 'Married' },
  { value: 'other', label: 'Other' },
] as const;

const PERSON_TYPE_CHIPS = [
  { value: 'partner', label: 'Partner' },
  { value: 'child', label: 'Child' },
  { value: 'parent', label: 'Parent' },
  { value: 'sibling', label: 'Sibling' },
  { value: 'friend', label: 'Close friend' },
  { value: 'other', label: 'Other' },
] as const;

const EXPENSE_LABELS: Record<ExpenseCategoryId, string> = {
  insurance: 'Insurance',
  debt: 'Debt payments',
  subscription: 'Subscriptions',
  utilities: 'Utilities',
  other: 'Other',
  groceries: 'Groceries',
  healthcare: 'Healthcare',
  childcare: 'Childcare',
};

function statusDotClass(status: ModuleState['status']): string {
  switch (status) {
    case 'pending':
      return 'h-2 w-2 shrink-0 rounded-full bg-slate-300';
    case 'active':
    case 'in_progress':
      return 'h-2 w-2 shrink-0 rounded-full bg-[#5B2D8E] animate-pulse';
    case 'complete':
      return 'h-2 w-2 shrink-0 rounded-full bg-green-500';
    case 'skipped':
      return 'h-2 w-2 shrink-0 rounded-full bg-amber-500';
    default:
      return 'h-2 w-2 shrink-0 rounded-full bg-slate-300';
  }
}

function toBool(raw: unknown): boolean {
  return raw === true || raw === 'true' || raw === 1 || raw === '1';
}

function coerceField(moduleId: ModuleId, path: string, raw: unknown): unknown {
  if (moduleId === 'vehicle' && path === 'vehicle_count') {
    const n = typeof raw === 'string' ? parseInt(raw, 10) : Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
  if (moduleId === 'income' && path === 'has_secondary') {
    return toBool(raw);
  }
  if (moduleId === 'housing' && path === 'has_buy_goal') {
    return toBool(raw);
  }
  if (moduleId === 'career' && path === 'open_to_move') {
    return toBool(raw);
  }
  if (moduleId === 'career' && path === 'satisfaction') {
    const n = typeof raw === 'string' ? parseInt(raw, 10) : Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
  if (path.endsWith('.recent_maintenance')) {
    return toBool(raw);
  }
  return raw;
}

function fakeCommit(path: string, stored: unknown): CommitFieldResponse {
  return {
    ok: true,
    changed: true,
    committed_at: new Date().toISOString(),
    field_path: path,
    value_stored: stored,
  };
}

export interface ModulePanelProps {
  moduleId: ModuleId;
  moduleState: ModuleState;
  data: ModuleData;
  onEditField: (
    fieldPath: string,
    value: unknown
  ) => Promise<CommitFieldResponse | undefined>;
  onSkip: () => Promise<void>;
  onCommit: () => Promise<CommitModuleResponse | undefined>;
  userTier: 'budget' | 'mid_tier' | 'professional' | null;
}

export function ModulePanel({
  moduleId,
  moduleState,
  data,
  onEditField,
  onSkip,
  onCommit,
  userTier,
}: ModulePanelProps) {
  const [isCommitting, setIsCommitting] = useState(false);
  const [commitError, setCommitError] = useState<string | null>(null);
  const [ephemeralRecurring, setEphemeralRecurring] = useState<
    Record<number, boolean | undefined>
  >({});

  const doCommit = useCallback(
    async (path: string, raw: unknown) => {
      return onEditField(path, coerceField(moduleId, path, raw));
    },
    [moduleId, onEditField]
  );

  const handleCommit = useCallback(async () => {
    setIsCommitting(true);
    setCommitError(null);
    try {
      await onCommit();
    } catch (e) {
      setCommitError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setIsCommitting(false);
    }
  }, [onCommit]);

  const showCommit =
    moduleState.status === 'active' || moduleState.status === 'in_progress';

  const gridClass = 'grid grid-cols-2 gap-3 sm:grid-cols-3';

  const income = data.income;
  const housing = data.housing;
  const vehicle = data.vehicle;
  const roster = data.roster;
  const career = data.career;
  const milestones = data.milestones;

  const zipMode =
    housing.zip_or_city != null &&
    housing.zip_or_city !== '' &&
    /^\d{5}$/.test(String(housing.zip_or_city).trim());

  let body: ReactElement | null = null;

  if (moduleId === 'income') {
    body = (
      <div className={gridClass}>
        <ChipField
          label="Monthly take-home"
          value={income.monthly_takehome}
          fieldPath="monthly_takehome"
          inputMode="currency"
          onCommit={doCommit}
        />
        <ChipField
          label="Pay frequency"
          value={income.pay_frequency}
          fieldPath="pay_frequency"
          inputMode="chip_select"
          chips={[...PAY_FREQUENCY_CHIPS]}
          onCommit={doCommit}
        />
        <ChipField
          label="Secondary income?"
          value={income.has_secondary}
          fieldPath="has_secondary"
          inputMode="chip_select"
          chips={[...YES_NO_CHIPS]}
          onCommit={doCommit}
        />
        {income.has_secondary === true && (
          <ChipField
            label="Secondary amount"
            value={income.secondary_amount}
            fieldPath="secondary_amount"
            inputMode="currency"
            onCommit={doCommit}
          />
        )}
        <ChipField
          label="Bonus cadence"
          value={income.bonus_cadence}
          fieldPath="bonus_cadence"
          inputMode="text"
          maxLength={200}
          onCommit={doCommit}
          hint="(saved in session only)"
        />
      </div>
    );
  } else if (moduleId === 'housing') {
    body = (
      <div className={gridClass}>
        <ChipField
          label="Rent or own"
          value={housing.housing_type}
          fieldPath="housing_type"
          inputMode="chip_select"
          chips={[...HOUSING_TYPE_CHIPS]}
          onCommit={doCommit}
        />
        <ChipField
          label="Monthly cost"
          value={housing.monthly_cost}
          fieldPath="monthly_cost"
          inputMode="currency"
          onCommit={doCommit}
        />
        <ChipField
          label="ZIP or city"
          value={housing.zip_or_city}
          fieldPath="zip_or_city"
          inputMode={zipMode ? 'zip' : 'text'}
          maxLength={zipMode ? 5 : 120}
          onCommit={doCommit}
        />
        {housing.split_share_pct != null && (
          <ChipField
            label="Split %"
            value={housing.split_share_pct}
            fieldPath="split_share_pct"
            inputMode="number"
            min={0}
            max={100}
            onCommit={doCommit}
          />
        )}
        <ChipField
          label="Buying goal?"
          value={housing.has_buy_goal}
          fieldPath="has_buy_goal"
          inputMode="chip_select"
          chips={[...YES_NO_CHIPS]}
          onCommit={doCommit}
        />
        {housing.has_buy_goal === true && (
          <>
            <ChipField
              label="Target price"
              value={housing.target_price}
              fieldPath="target_price"
              inputMode="currency"
              onCommit={doCommit}
            />
            <ChipField
              label="Timeline (months)"
              value={housing.target_timeline_months}
              fieldPath="target_timeline_months"
              inputMode="number"
              min={0}
              max={60}
              onCommit={doCommit}
            />
          </>
        )}
      </div>
    );
  } else if (moduleId === 'vehicle') {
    const rows = vehicle.vehicles ?? [];
    const count = vehicle.vehicle_count ?? 0;
    body = (
      <div className={gridClass}>
        <ChipField
          label="Vehicle count"
          value={String(count)}
          fieldPath="vehicle_count"
          inputMode="chip_select"
          chips={[...VEHICLE_COUNT_CHIPS]}
          onCommit={doCommit}
        />
        {rows.map((v, i) => (
          <div
            key={i}
            className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-3 sm:grid-cols-3"
          >
            <ChipField
              label={`Vehicle ${i + 1} — Make`}
              value={v.make}
              fieldPath={`vehicles[${i}].make`}
              inputMode="text"
              onCommit={doCommit}
            />
            <ChipField
              label={`Vehicle ${i + 1} — Model`}
              value={v.model}
              fieldPath={`vehicles[${i}].model`}
              inputMode="text"
              onCommit={doCommit}
            />
            <ChipField
              label={`Vehicle ${i + 1} — Year`}
              value={v.year}
              fieldPath={`vehicles[${i}].year`}
              inputMode="year"
              min={MIN_VEHICLE_YEAR}
              max={MAX_VEHICLE_YEAR}
              onCommit={doCommit}
            />
            <ChipField
              label={`Vehicle ${i + 1} — Monthly fuel`}
              value={v.monthly_fuel}
              fieldPath={`vehicles[${i}].monthly_fuel`}
              inputMode="currency"
              onCommit={doCommit}
            />
            <ChipField
              label={`Vehicle ${i + 1} — Monthly payment`}
              value={v.monthly_payment}
              fieldPath={`vehicles[${i}].monthly_payment`}
              inputMode="currency"
              onCommit={doCommit}
            />
            <ChipField
              label={`Vehicle ${i + 1} — Recent maint?`}
              value={v.recent_maintenance}
              fieldPath={`vehicles[${i}].recent_maintenance`}
              inputMode="chip_select"
              chips={[...YES_NO_CHIPS]}
              onCommit={doCommit}
            />
          </div>
        ))}
        {count > rows.length && (
          <div className="col-span-2 sm:col-span-3">
            <button
              type="button"
              onClick={() => void doCommit('vehicles[new].make', '')}
              className="w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm font-medium text-slate-600 transition-colors hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
            >
              + Add vehicle
            </button>
          </div>
        )}
      </div>
    );
  } else if (moduleId === 'recurring_expenses') {
    const cats = data.recurring_expenses.categories ?? {};
    body = (
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {EXPENSE_CATEGORY_IDS.map((id) => (
          <ChipField
            key={id}
            label={EXPENSE_LABELS[id]}
            value={cats[id]}
            fieldPath={`categories[${id}].amount`}
            inputMode="currency"
            onCommit={doCommit}
            emptyPlaceholder="Not set"
          />
        ))}
      </div>
    );
  } else if (moduleId === 'roster') {
    const people = roster.people ?? [];
    body = (
      <div className={gridClass}>
        <ChipField
          label="Relationship status"
          value={roster.relationship_status}
          fieldPath="relationship_status"
          inputMode="chip_select"
          chips={[...RELATIONSHIP_CHIPS]}
          onCommit={doCommit}
        />
        {people.map((p, i) => (
          <div
            key={i}
            className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-3 sm:grid-cols-3"
          >
            <ChipField
              label={`Person ${i + 1} — Nickname`}
              value={p.nickname}
              fieldPath={`people[${i}].nickname`}
              inputMode="text"
              maxLength={30}
              onCommit={doCommit}
            />
            <ChipField
              label={`Person ${i + 1} — Type`}
              value={p.relationship_type}
              fieldPath={`people[${i}].relationship_type`}
              inputMode="chip_select"
              chips={[...PERSON_TYPE_CHIPS]}
              onCommit={doCommit}
            />
            <ChipField
              label={`Person ${i + 1} — Monthly cost`}
              value={p.monthly_cost}
              fieldPath={`people[${i}].monthly_cost`}
              inputMode="currency"
              onCommit={doCommit}
            />
          </div>
        ))}
        <div className="col-span-2 sm:col-span-3">
          <button
            type="button"
            onClick={() => void doCommit('people[new].nickname', '')}
            className="w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm font-medium text-slate-600 transition-colors hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
          >
            + Add person
          </button>
        </div>
        <ChipField
          label="Monthly social spend"
          value={roster.monthly_social_spend}
          fieldPath="monthly_social_spend"
          inputMode="currency"
          onCommit={doCommit}
        />
      </div>
    );
  } else if (moduleId === 'career') {
    const satChips = [1, 2, 3, 4, 5].map((n) => ({
      value: String(n),
      label: String(n),
    }));
    body = (
      <div className={gridClass}>
        <ChipField
          label="Current role"
          value={career.current_role}
          fieldPath="current_role"
          inputMode="text"
          maxLength={100}
          onCommit={doCommit}
        />
        <ChipField
          label="Industry"
          value={career.industry}
          fieldPath="industry"
          inputMode="text"
          maxLength={100}
          onCommit={doCommit}
        />
        <ChipField
          label="Years experience"
          value={career.years_experience}
          fieldPath="years_experience"
          inputMode="number"
          min={0}
          max={60}
          onCommit={doCommit}
        />
        <ChipField
          label="Satisfaction"
          value={
            career.satisfaction == null ? undefined : String(career.satisfaction)
          }
          fieldPath="satisfaction"
          inputMode="chip_select"
          chips={satChips}
          onCommit={doCommit}
        />
        <ChipField
          label="Open to move?"
          value={career.open_to_move}
          fieldPath="open_to_move"
          inputMode="chip_select"
          chips={[...YES_NO_CHIPS]}
          onCommit={doCommit}
        />
        {career.open_to_move === true && userTier !== 'budget' && (
          <ChipField
            label="Target comp"
            value={career.target_comp}
            fieldPath="target_comp"
            inputMode="currency"
            onCommit={doCommit}
          />
        )}
      </div>
    );
  } else if (moduleId === 'milestones') {
    const events = milestones.events ?? [];
    body = (
      <div className={gridClass}>
        {events.length === 0 && (
          <div className="col-span-2 flex justify-center sm:col-span-3">
            <button
              type="button"
              onClick={() => void doCommit('events[new].name', '')}
              className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 py-4 text-sm font-medium text-slate-600 transition-colors hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
            >
              Nothing upcoming — tap to add
            </button>
          </div>
        )}
        {events.map((ev, i) => (
          <div
            key={i}
            className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-3 sm:grid-cols-3"
          >
            <ChipField
              label={`Event ${i + 1} — Name`}
              value={ev.name}
              fieldPath={`events[${i}].name`}
              inputMode="text"
              maxLength={100}
              onCommit={doCommit}
            />
            <ChipField
              label={`Event ${i + 1} — Date`}
              value={ev.date}
              fieldPath={`events[${i}].date`}
              inputMode="date"
              onCommit={doCommit}
            />
            <ChipField
              label={`Event ${i + 1} — Cost`}
              value={ev.cost}
              fieldPath={`events[${i}].cost`}
              inputMode="currency"
              onCommit={doCommit}
            />
            <ChipField
              label={`Event ${i + 1} — Recurring?`}
              value={
                ephemeralRecurring[i] !== undefined
                  ? ephemeralRecurring[i]
                  : ev.recurring
              }
              fieldPath={`events[${i}].recurring`}
              inputMode="chip_select"
              chips={[...YES_NO_CHIPS]}
              onCommit={async (path, v) => {
                const b = toBool(v);
                setEphemeralRecurring((prev) => ({ ...prev, [i]: b }));
                return fakeCommit(path, b);
              }}
              hint="(saved in session only)"
            />
          </div>
        ))}
        {events.length > 0 && (
          <div className="col-span-2 sm:col-span-3">
            <button
              type="button"
              onClick={() => void doCommit('events[new].name', '')}
              className="w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm font-medium text-slate-600 transition-colors hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
            >
              + Add milestone
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border-[1.5px] bg-white p-6 shadow-sm">
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={statusDotClass(moduleState.status)} />
          <h2 className="text-lg font-bold text-slate-900">
            {moduleState.display_name}
          </h2>
        </div>
        {(moduleState.status === 'active' ||
          moduleState.status === 'in_progress') && (
          <button
            type="button"
            onClick={() => void onSkip()}
            className="text-sm text-slate-500 hover:text-[#5B2D8E] hover:underline"
          >
            Skip for now
          </button>
        )}
      </header>
      {body}
      {commitError && (
        <p className="mt-3 text-sm text-[#DC2626]">{commitError}</p>
      )}
      {showCommit && (
        <button
          type="button"
          onClick={() => void handleCommit()}
          className="mt-4 w-full rounded-lg bg-[#5B2D8E] py-3 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          disabled={isCommitting}
        >
          {isCommitting ? 'Saving...' : 'Looks right — move on'}
        </button>
      )}
    </div>
  );
}
