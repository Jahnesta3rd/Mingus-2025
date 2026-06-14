import React, { useCallback, useEffect, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { CHECKLIST_ITEMS, type ChecklistItem } from '../data/parentChecklist';
import { csrfHeaders } from '../utils/csrfHeaders';

interface NewParentChecklistCardProps {
  userId: string;
  completedIds: string[];
  onUpdate: (ids: string[]) => void;
  hasBabyMilestone?: boolean;
  className?: string;
  isLoading?: boolean;
  profileError?: boolean;
  onViewForecast?: () => void;
}

const TOTAL_ITEMS = 12;

const IMPACT_ITEMS = new Set([
  'open_529',
  'life_insurance_will',
  'short_term_disability',
  'childcare_waitlist',
]);

const IMPACT_NAME_TO_ID: Record<string, string> = {
  '529 college savings': 'open_529',
  'Life insurance premium': 'life_insurance_will',
  'Short-term disability': 'short_term_disability',
  Childcare: 'childcare_waitlist',
};

const URGENCY_DOT: Record<ChecklistItem['urgency'], string> = {
  high: 'bg-red-400',
  medium: 'bg-amber-400',
  low: 'bg-gray-300',
};

function Toast({ message }: { message: string }) {
  return (
    <div
      className="absolute top-4 right-4 z-10 rounded-lg bg-gray-800 px-4 py-2 text-sm text-white shadow-md"
      role="status"
    >
      {message}
    </div>
  );
}

async function patchChecklist(userId: string, ids: string[]): Promise<boolean> {
  const token = localStorage.getItem('mingus_token');
  const response = await fetch('/api/user/profile', {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      ...csrfHeaders(),
      Authorization: `Bearer ${token ?? ''}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      important_dates: { parent_checklist: ids },
    }),
  });
  return response.ok;
}

function fireApplyImpact(itemId: string, onSuccess: (amount: number) => void): void {
  const token = localStorage.getItem('mingus_token');
  fetch('/api/user/checklist/apply-impact', {
    method: 'POST',
    credentials: 'include',
    headers: {
      ...csrfHeaders(),
      Authorization: `Bearer ${token ?? ''}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ item_id: itemId }),
  })
    .then((r) => (r.ok ? r.json() : null))
    .then((data: { amount?: number } | null) => {
      if (data != null && typeof data.amount === 'number') {
        onSuccess(data.amount);
      }
    })
    .catch(() => {});
}

function formatMonthly(amount: number): string {
  return `$${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}/month`;
}

function ChecklistItemRow({
  item,
  checked,
  impactAmount,
  onToggle,
}: {
  item: ChecklistItem;
  checked: boolean;
  impactAmount?: number;
  onToggle: () => void;
}) {
  const textMuted = checked ? 'text-gray-400' : 'text-gray-800';
  const bodyMuted = checked ? 'text-gray-400' : 'text-gray-500';

  return (
    <div className="flex items-start gap-3">
      <button
        type="button"
        onClick={onToggle}
        aria-checked={checked}
        role="checkbox"
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
          checked ? 'border-teal-500 bg-teal-500' : 'border-gray-300 bg-white'
        }`}
      >
        {checked ? (
          <svg viewBox="0 0 12 12" className="h-3 w-3 text-white" aria-hidden="true">
            <path
              d="M2 6l3 3 5-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : null}
      </button>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center">
          <span className="mr-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
            {item.number}
          </span>
          <span className={`text-sm font-medium ${textMuted}`}>{item.title}</span>
          <span
            className={`ml-1 inline-block h-2 w-2 rounded-full ${URGENCY_DOT[item.urgency]}`}
            aria-hidden="true"
          />
          {item.badge ? (
            <span className="ml-2 rounded-full border border-teal-500 px-2 py-0.5 text-xs text-teal-600">
              {item.badge}
            </span>
          ) : null}
        </div>
        <p className={`mt-0.5 text-sm ${bodyMuted}`}>{item.body}</p>
        {checked && impactAmount != null ? (
          <p className="mt-0.5 text-xs text-teal-600">
            Added {formatMonthly(impactAmount)} to your forecast ✓
          </p>
        ) : null}
      </div>
    </div>
  );
}

export default function NewParentChecklistCard({
  userId,
  completedIds,
  onUpdate,
  hasBabyMilestone = false,
  className = '',
  isLoading = false,
  profileError = false,
  onViewForecast,
}: NewParentChecklistCardProps) {
  const [manuallyOpened, setManuallyOpened] = useState(false);
  const [completedExpanded, setCompletedExpanded] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [impactConfirmed, setImpactConfirmed] = useState<Map<string, number>>(() => new Map());

  const expanded = hasBabyMilestone || manuallyOpened;
  const completedSet = new Set(completedIds);
  const completedCount = completedIds.length;
  const activeItems = CHECKLIST_ITEMS.filter((item) => !completedSet.has(item.id));
  const doneItems = CHECKLIST_ITEMS.filter((item) => completedSet.has(item.id));
  const impactMonthlyTotal = Array.from(impactConfirmed.values()).reduce((sum, n) => sum + n, 0);

  useEffect(() => {
    const token = localStorage.getItem('mingus_token');
    fetch('/api/user/checklist/impact-summary', {
      credentials: 'include',
      headers: {
        ...csrfHeaders(),
        Authorization: `Bearer ${token ?? ''}`,
        'Content-Type': 'application/json',
      },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { items?: Array<{ name: string; amount: number }> } | null) => {
        if (!data?.items?.length) return;
        const map = new Map<string, number>();
        for (const row of data.items) {
          const id = IMPACT_NAME_TO_ID[row.name];
          if (id) map.set(id, row.amount);
        }
        if (map.size > 0) setImpactConfirmed(map);
      })
      .catch(() => {});
  }, []);

  const confirmImpact = useCallback((itemId: string, amount: number) => {
    setImpactConfirmed((prev) => {
      const next = new Map(prev);
      next.set(itemId, amount);
      return next;
    });
  }, []);

  const maybeApplyImpact = useCallback(
    (itemId: string, wasChecked: boolean) => {
      if (wasChecked || !IMPACT_ITEMS.has(itemId)) return;
      fireApplyImpact(itemId, (amount) => confirmImpact(itemId, amount));
    },
    [confirmImpact]
  );

  const showToast = useCallback((message: string) => {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 3000);
  }, []);

  const persistIds = useCallback(
    async (nextIds: string[], prevIds: string[]) => {
      onUpdate(nextIds);
      const ok = await patchChecklist(userId, nextIds);
      if (!ok) {
        onUpdate(prevIds);
        showToast('Could not save — tap to retry');
      }
    },
    [onUpdate, showToast, userId]
  );

  const handleToggle = useCallback(
    (id: string) => {
      const wasChecked = completedIds.includes(id);
      const next = wasChecked ? completedIds.filter((x) => x !== id) : [...completedIds, id];
      maybeApplyImpact(id, wasChecked);
      void persistIds(next, completedIds);
    },
    [completedIds, maybeApplyImpact, persistIds]
  );

  const handleMarkAllDone = useCallback(() => {
    const prev = completedIds;
    const next = CHECKLIST_ITEMS.map((item) => item.id);
    for (const item of CHECKLIST_ITEMS) {
      if (!prev.includes(item.id)) {
        maybeApplyImpact(item.id, false);
      }
    }
    void persistIds(next, prev);
  }, [completedIds, maybeApplyImpact, persistIds]);

  if (isLoading) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`} role="status">
        <div className="mb-4 h-5 w-56 animate-pulse rounded bg-gray-100" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      </div>
    );
  }

  if (profileError) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
        <p className="text-sm text-gray-600">Unable to load checklist. Tap to retry.</p>
        <button
          type="button"
          onClick={() => onUpdate([])}
          className="mt-3 text-sm font-medium text-teal-600 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setManuallyOpened(true)}
        className={`flex w-full items-center justify-between rounded-xl border border-gray-200 bg-gray-50 p-4 text-left ${className}`}
      >
        <span className="text-sm text-gray-600">Planning for a baby? See financial checklist</span>
        <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" aria-hidden="true" />
      </button>
    );
  }

  return (
    <div className={`relative rounded-xl bg-white p-6 shadow-sm ${className}`}>
      {toastMessage ? <Toast message={toastMessage} /> : null}

      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-gray-800">New Parent Financial Checklist</h2>
          <p className="text-sm text-gray-500">12 things that catch parents off guard</p>
        </div>
        <span className="shrink-0 text-sm text-gray-500">
          {completedCount} / {TOTAL_ITEMS} done
        </span>
      </div>

      <div className="mt-3 h-1.5 rounded-full bg-gray-100">
        <div
          className="h-1.5 rounded-full bg-teal-500 transition-all"
          style={{ width: `${(completedCount / TOTAL_ITEMS) * 100}%` }}
        />
      </div>

      {completedCount < TOTAL_ITEMS ? (
        <button
          type="button"
          onClick={handleMarkAllDone}
          className="mt-3 text-sm text-teal-600 underline"
        >
          Mark all done
        </button>
      ) : null}

      <div className="mt-4 max-h-[480px] space-y-3 overflow-y-auto">
        {activeItems.map((item) => (
          <ChecklistItemRow
            key={item.id}
            item={item}
            checked={false}
            impactAmount={impactConfirmed.get(item.id)}
            onToggle={() => handleToggle(item.id)}
          />
        ))}

        {doneItems.length > 0 && !completedExpanded ? (
          <button
            type="button"
            onClick={() => setCompletedExpanded(true)}
            className="flex w-full items-center gap-1 text-sm text-gray-500"
          >
            <span>{doneItems.length} completed</span>
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}

        {completedExpanded
          ? doneItems.map((item) => (
              <ChecklistItemRow
                key={item.id}
                item={item}
                checked
                impactAmount={impactConfirmed.get(item.id)}
                onToggle={() => handleToggle(item.id)}
              />
            ))
          : null}
      </div>

      {impactConfirmed.size > 0 ? (
        <div className="mt-4 flex items-center justify-between rounded-xl border border-teal-200 bg-teal-50 px-4 py-3">
          <div>
            <p className="text-sm font-medium text-teal-800">Added to your forecast</p>
            <p className="text-xs text-teal-600">
              {formatMonthly(impactMonthlyTotal)} in recurring costs
            </p>
          </div>
          <button
            type="button"
            onClick={() => onViewForecast?.()}
            className="text-xs text-teal-600 underline"
          >
            View forecast →
          </button>
        </div>
      ) : null}

      <p className="mt-4 text-xs text-gray-400">
        Based on real parent experience. Not financial advice.
      </p>
    </div>
  );
}
