import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { useConversationalOnboarding } from '../hooks/useConversationalOnboarding';
import type {
  ConvCluster,
  ExtractedData,
  ExtractedExpense,
  ExtractedIncome,
  ExtractedMilestone,
} from '../types/conversationalOnboarding';

const BRAND_PURPLE = '#5B2D8E';

const HARD_CAP_COPY =
  "We've been at this a while.\nLet me show you what I have so far — you can fill in the rest on your dashboard.";

interface ConversationalOnboardingProps {
  onComplete: () => void;
}

function clusterIndex(c: ConvCluster): number {
  if (c === 'income') return 0;
  if (c === 'expenses') return 1;
  if (c === 'milestones') return 2;
  return 3;
}

function emptyIncome(): ExtractedIncome {
  return {
    monthly_takehome: 0,
    has_secondary: false,
    secondary_amount: null,
  };
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

function parseMoney(raw: string): number {
  const n = parseFloat(raw.replace(/[^0-9.-]/g, ''));
  return Number.isFinite(n) ? n : 0;
}

function CheckIcon() {
  return (
    <svg className="h-3 w-3 text-white" viewBox="0 0 12 12" fill="none" aria-hidden>
      <path
        d="M2.5 6L5 8.5L9.5 3.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ClusterProgressBar({
  cluster,
  phase,
}: {
  cluster: ConvCluster;
  phase: string;
}) {
  const currentIdx = clusterIndex(cluster);
  const allDone =
    cluster === 'done' || phase === 'committing' || phase === 'complete';

  const lineAfter = (stepIdx: number) => {
    if (allDone) return true;
    return currentIdx > stepIdx;
  };

  const stepVisual = (idx: number, label: string) => {
    let status: 'completed' | 'active' | 'upcoming';
    if (allDone || currentIdx > idx) status = 'completed';
    else if (currentIdx === idx) status = 'active';
    else status = 'upcoming';

    return (
      <div key={label} className="flex flex-1 flex-col items-center min-w-0">
        <div
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
            status === 'completed'
              ? 'bg-[#5B2D8E] text-white'
              : status === 'active'
                ? 'border-2 border-[#5B2D8E] bg-white text-[#5B2D8E]'
                : 'border-2 border-gray-300 bg-white text-gray-400'
          }`}
        >
          {status === 'completed' ? <CheckIcon /> : idx + 1}
        </div>
        <span
          className={`mt-1 max-w-[5.5rem] truncate text-center text-[11px] sm:text-xs ${
            status === 'completed' || status === 'active'
              ? 'font-bold text-[#5B2D8E]'
              : 'font-medium text-gray-500'
          }`}
        >
          {label}
        </span>
      </div>
    );
  };

  return (
    <div className="flex w-full max-w-md items-start justify-center px-1">
      <div className="flex w-full items-start">
        {stepVisual(0, 'Income')}
        <div className="mx-1 flex flex-1 items-center pt-[13px]">
          <div
            className={`h-0.5 w-full rounded-full ${lineAfter(0) ? 'bg-[#5B2D8E]' : 'bg-gray-200'}`}
          />
        </div>
        {stepVisual(1, 'Expenses')}
        <div className="mx-1 flex flex-1 items-center pt-[13px]">
          <div
            className={`h-0.5 w-full rounded-full ${lineAfter(1) ? 'bg-[#5B2D8E]' : 'bg-gray-200'}`}
          />
        </div>
        {stepVisual(2, 'Milestones')}
      </div>
    </div>
  );
}

export default function ConversationalOnboarding({ onComplete }: ConversationalOnboardingProps) {
  const {
    messages,
    cluster,
    phase,
    extracted,
    pendingExtraction,
    isTyping,
    turnCount,
    error,
    sendMessage,
    confirmCluster,
    resetConversation,
  } = useConversationalOnboarding();

  const scrollRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState('');

  const [incomeDraft, setIncomeDraft] = useState<ExtractedIncome>(emptyIncome);
  const [expenseDraft, setExpenseDraft] = useState<ExtractedExpense[]>([]);
  const [milestoneDraft, setMilestoneDraft] = useState<ExtractedMilestone[]>([]);

  const showConfirmCard = phase === 'confirming' || phase === 'hard_cap';

  const displayMessages =
    phase === 'hard_cap'
      ? (() => {
          let lastAi = -1;
          for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].role === 'assistant') {
              lastAi = i;
              break;
            }
          }
          if (lastAi < 0) return messages;
          return messages.map((m, i) =>
            i === lastAi ? { ...m, content: HARD_CAP_COPY } : m,
          );
        })()
      : messages;

  const inputLocked =
    phase === 'confirming' || phase === 'committing' || phase === 'complete';

  useEffect(() => {
    if (!showConfirmCard) return;

    const base =
      pendingExtraction ??
      ({
        income: extracted.income,
        expenses: extracted.expenses,
        milestones: extracted.milestones,
      } as Partial<ExtractedData>);

    if (cluster === 'income') {
      setIncomeDraft(
        base.income
          ? { ...base.income }
          : extracted.income
            ? { ...extracted.income }
            : emptyIncome(),
      );
    } else if (cluster === 'expenses') {
      const rows = base.expenses?.length
        ? base.expenses.map((e) => ({ ...e }))
        : extracted.expenses.length
          ? extracted.expenses.map((e) => ({ ...e }))
          : [{ name: '', amount: 0 }];
      setExpenseDraft(rows);
    } else if (cluster === 'milestones') {
      const rows = base.milestones?.length
        ? base.milestones.map((m) => ({ ...m }))
        : extracted.milestones.length
          ? extracted.milestones.map((m) => ({ ...m }))
          : [];
      setMilestoneDraft(rows);
    }
  }, [showConfirmCard, cluster, pendingExtraction, extracted]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, phase, isTyping, showConfirmCard, error]);

  useEffect(() => {
    if (phase !== 'complete') return;
    const t = window.setTimeout(() => {
      onComplete();
    }, 1500);
    return () => window.clearTimeout(t);
  }, [phase, onComplete]);

  const handleSend = useCallback(() => {
    const t = inputValue.trim();
    if (!t || inputLocked) return;
    void sendMessage(t);
    setInputValue('');
  }, [inputValue, inputLocked, sendMessage]);

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  const submitIncomeConfirm = () => {
    void confirmCluster({
      income: {
        ...incomeDraft,
        secondary_amount: incomeDraft.has_secondary ? incomeDraft.secondary_amount : null,
      },
    });
  };

  const submitExpensesConfirm = () => {
    const cleaned = expenseDraft
      .filter((r) => r.name.trim() !== '')
      .map((r) => ({ ...r, name: r.name.trim(), amount: Number(r.amount) || 0 }));
    void confirmCluster({ expenses: cleaned });
  };

  const submitMilestonesConfirm = () => {
    const cleaned = milestoneDraft
      .filter((r) => r.name.trim() !== '')
      .map((r) => ({
        ...r,
        name: r.name.trim(),
        date_hint: r.date_hint.trim(),
        cost: Number(r.cost) || 0,
      }));
    void confirmCluster({ milestones: cleaned });
  };

  const renderConfirmCard = () => {
    if (!showConfirmCard || cluster === 'done') return null;

    if (cluster === 'income') {
      return (
        <div
          className="mt-3 w-full rounded-2xl border-[1.5px] bg-white p-4 shadow-sm"
          style={{ borderColor: BRAND_PURPLE }}
        >
          <h3 className="mb-3 text-sm font-bold text-[#5B2D8E]">
            Here&apos;s what I heard — income
          </h3>
          <label className="mb-3 block text-sm text-gray-700">
            <span className="mb-1 block text-xs text-gray-500">Monthly take-home</span>
            <div className="flex overflow-hidden rounded-lg border border-gray-200">
              <span className="flex items-center bg-gray-50 px-3 text-gray-600">$</span>
              <input
                type="number"
                className="min-w-0 flex-1 border-0 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                value={incomeDraft.monthly_takehome || ''}
                onChange={(e) =>
                  setIncomeDraft((d) => ({
                    ...d,
                    monthly_takehome: parseMoney(e.target.value),
                  }))
                }
              />
            </div>
          </label>
          {incomeDraft.has_secondary && (
            <label className="mb-3 block text-sm text-gray-700">
              <span className="mb-1 block text-xs text-gray-500">Secondary / side income</span>
              <div className="flex overflow-hidden rounded-lg border border-gray-200">
                <span className="flex items-center bg-gray-50 px-3 text-gray-600">$</span>
                <input
                  type="number"
                  className="min-w-0 flex-1 border-0 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                  value={incomeDraft.secondary_amount ?? ''}
                  onChange={(e) =>
                    setIncomeDraft((d) => ({
                      ...d,
                      secondary_amount: parseMoney(e.target.value),
                    }))
                  }
                />
              </div>
            </label>
          )}
          <div className="mb-4">
            <span className="mb-2 block text-xs text-gray-500">Side/gig income?</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() =>
                  setIncomeDraft((d) => ({
                    ...d,
                    has_secondary: true,
                    secondary_amount: d.secondary_amount ?? 0,
                  }))
                }
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  incomeDraft.has_secondary
                    ? 'bg-[#5B2D8E] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Yes
              </button>
              <button
                type="button"
                onClick={() =>
                  setIncomeDraft((d) => ({
                    ...d,
                    has_secondary: false,
                    secondary_amount: null,
                  }))
                }
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  !incomeDraft.has_secondary
                    ? 'bg-[#5B2D8E] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                No
              </button>
            </div>
          </div>
          <button
            type="button"
            disabled={phase === 'confirmed'}
            onClick={submitIncomeConfirm}
            className="w-full rounded-lg bg-[#5B2D8E] py-3 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            Looks right →
          </button>
          <p className="mt-2 text-center text-[11px] text-gray-500">
            Tap any value above to edit before confirming
          </p>
        </div>
      );
    }

    if (cluster === 'expenses') {
      return (
        <div
          className="mt-3 w-full rounded-2xl border-[1.5px] bg-white p-4 shadow-sm"
          style={{ borderColor: BRAND_PURPLE }}
        >
          <h3 className="mb-3 text-sm font-bold text-[#5B2D8E]">
            Here&apos;s what I heard — expenses
          </h3>
          {expenseDraft.map((row, i) => (
            <div key={i} className="mb-2 flex gap-2">
              <input
                type="text"
                placeholder="Name"
                className="min-w-0 flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                value={row.name}
                onChange={(e) => {
                  const next = [...expenseDraft];
                  next[i] = { ...next[i], name: e.target.value };
                  setExpenseDraft(next);
                }}
              />
              <div className="flex w-28 shrink-0 overflow-hidden rounded-lg border border-gray-200 sm:w-36">
                <span className="flex items-center bg-gray-50 px-2 text-gray-600 text-xs">$</span>
                <input
                  type="number"
                  className="min-w-0 w-full border-0 px-2 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                  value={row.amount || ''}
                  onChange={(e) => {
                    const next = [...expenseDraft];
                    next[i] = { ...next[i], amount: parseMoney(e.target.value) };
                    setExpenseDraft(next);
                  }}
                />
              </div>
            </div>
          ))}
          <button
            type="button"
            className="mb-4 text-sm font-medium text-[#5B2D8E] hover:underline"
            onClick={() => setExpenseDraft((d) => [...d, { name: '', amount: 0 }])}
          >
            Add another
          </button>
          <button
            type="button"
            disabled={phase === 'confirmed'}
            onClick={submitExpensesConfirm}
            className="w-full rounded-lg bg-[#5B2D8E] py-3 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            Looks right →
          </button>
        </div>
      );
    }

    if (cluster === 'milestones') {
      return (
        <div
          className="mt-3 w-full rounded-2xl border-[1.5px] bg-white p-4 shadow-sm"
          style={{ borderColor: BRAND_PURPLE }}
        >
          <h3 className="mb-3 text-sm font-bold text-[#5B2D8E]">
            Here&apos;s what I heard — upcoming
          </h3>
          {milestoneDraft.length === 0 ? (
            <p className="mb-4 text-sm text-gray-600">
              Nothing upcoming logged. You can add events later.
            </p>
          ) : (
            milestoneDraft.map((row, i) => (
              <div key={i} className="mb-2 flex flex-col gap-2 sm:flex-row">
                <input
                  type="text"
                  placeholder="Name"
                  className="min-w-0 flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                  value={row.name}
                  onChange={(e) => {
                    const next = [...milestoneDraft];
                    next[i] = { ...next[i], name: e.target.value };
                    setMilestoneDraft(next);
                  }}
                />
                <input
                  type="text"
                  placeholder="Date hint"
                  className="min-w-0 flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                  value={row.date_hint}
                  onChange={(e) => {
                    const next = [...milestoneDraft];
                    next[i] = { ...next[i], date_hint: e.target.value };
                    setMilestoneDraft(next);
                  }}
                />
                <div className="flex w-full shrink-0 overflow-hidden rounded-lg border border-gray-200 sm:w-28">
                  <span className="flex items-center bg-gray-50 px-2 text-gray-600 text-xs">$</span>
                  <input
                    type="number"
                    className="min-w-0 w-full border-0 px-2 py-2 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                    value={row.cost || ''}
                    onChange={(e) => {
                      const next = [...milestoneDraft];
                      next[i] = { ...next[i], cost: parseMoney(e.target.value) };
                      setMilestoneDraft(next);
                    }}
                  />
                </div>
              </div>
            ))
          )}
          <button
            type="button"
            className="mb-4 text-sm font-medium text-[#5B2D8E] hover:underline"
            onClick={() =>
              setMilestoneDraft((d) => [...d, { name: '', date_hint: '', cost: 0 }])
            }
          >
            Add another
          </button>
          <button
            type="button"
            disabled={phase === 'confirmed'}
            onClick={submitMilestonesConfirm}
            className="w-full rounded-lg bg-[#5B2D8E] py-3 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            Looks right →
          </button>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gray-50" style={{ height: '100dvh' }}>
      <header className="fixed left-0 right-0 top-0 z-10 flex h-14 shrink-0 items-center border-b border-gray-200 bg-gray-50 px-3">
        <div className="flex w-full items-center justify-between gap-2">
          <div className="flex min-w-0 flex-shrink-0 items-center gap-2">
            <img src="/mingus-logo.png" alt="Mingus" className="h-7 w-auto object-contain" />
            <span className="hidden font-bold text-[#5B2D8E] sm:inline text-lg">Mingus</span>
          </div>
          <div className="min-w-0 flex-1 px-1">
            <ClusterProgressBar cluster={cluster} phase={phase} />
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1 text-right">
            <button
              type="button"
              onClick={() => onComplete()}
              className="whitespace-nowrap text-[12px] text-gray-500 hover:text-gray-700"
            >
              Skip for now →
            </button>
            <div className="flex items-center justify-end gap-2">
              {turnCount > 0 ? (
                <button
                  type="button"
                  onClick={() => onComplete()}
                  className="cursor-pointer text-xs text-gray-400 hover:text-gray-600"
                >
                  Exit →
                </button>
              ) : null}
              {turnCount >= 2 ? (
                <button
                  type="button"
                  onClick={() => void resetConversation()}
                  className="text-xs font-medium text-gray-500 hover:text-gray-700 sm:text-sm"
                >
                  Start over
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <div
        ref={scrollRef}
        className="mt-14 flex flex-1 flex-col overflow-y-auto px-4 pt-4"
        style={{ paddingBottom: 120 }}
      >
        <div className="mx-auto w-full max-w-lg flex-1">
          {displayMessages.map((m) => (
            <div key={m.id} className={`mb-4 flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'assistant' && (
                <div className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-xs font-bold text-white">
                  M
                </div>
              )}
              <div className={`max-w-[80%] ${m.role === 'user' ? 'ml-auto' : ''}`}>
                <div
                  className={`px-4 py-3 text-[15px] leading-[1.6] shadow-sm ${
                    m.role === 'assistant'
                      ? 'whitespace-pre-line rounded-2xl rounded-tl-none bg-white text-gray-900'
                      : 'rounded-2xl rounded-tr-none text-white'
                  }`}
                  style={m.role === 'user' ? { backgroundColor: BRAND_PURPLE } : undefined}
                >
                  {m.content}
                </div>
                <p className={`mt-1 text-[11px] text-gray-400 ${m.role === 'user' ? 'text-right' : ''}`}>
                  {formatTime(m.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="mb-4 flex justify-start">
              <div className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-xs font-bold text-white">
                M
              </div>
              <div className="max-w-[80%]">
                <div className="rounded-2xl rounded-tl-none bg-white px-4 py-3 text-[15px] leading-[1.6] text-gray-700 shadow-sm">
                  <span className="inline-flex gap-0.5">
                    <span className="animate-bounce" style={{ animationDelay: '0ms' }}>
                      •
                    </span>
                    <span className="animate-bounce" style={{ animationDelay: '150ms' }}>
                      •
                    </span>
                    <span className="animate-bounce" style={{ animationDelay: '300ms' }}>
                      •
                    </span>
                  </span>
                </div>
              </div>
            </div>
          )}

          {phase === 'committing' && (
            <div className="mb-4 flex justify-start">
              <div className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-xs font-bold text-white">
                M
              </div>
              <div className="max-w-[80%]">
                <div className="flex items-center gap-3 rounded-2xl rounded-tl-none bg-white px-4 py-3 text-[15px] leading-[1.6] text-gray-900 shadow-sm">
                  <span
                    className="inline-block h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-[#5B2D8E] border-t-transparent"
                    aria-hidden
                  />
                  One moment — saving your information...
                </div>
              </div>
            </div>
          )}

          {phase === 'complete' && (
            <div className="mb-4 flex justify-start">
              <div className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-xs font-bold text-white">
                M
              </div>
              <div className="max-w-[80%]">
                <div className="rounded-2xl rounded-tl-none bg-white px-4 py-3 text-[15px] leading-[1.6] text-gray-900 shadow-sm">
                  You&apos;re all set. Let&apos;s show you where you stand.
                </div>
              </div>
            </div>
          )}

          {phase === 'error' && error && (
            <div className="mb-4 flex justify-start">
              <div className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-xs font-bold text-white">
                M
              </div>
              <div className="max-w-[80%]">
                <div className="rounded-2xl rounded-tl-none bg-white px-4 py-3 text-[15px] leading-[1.6] text-gray-900 shadow-sm">
                  <p>{error}</p>
                  <button
                    type="button"
                    className="mt-2 text-sm font-semibold text-[#5B2D8E] hover:underline"
                    onClick={() => void resetConversation()}
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {renderConfirmCard()}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-lg gap-2">
          <input
            type="text"
            className="min-w-0 flex-1 rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-[#5B2D8E] focus:ring-2 focus:ring-[#5B2D8E]/20 disabled:bg-gray-50 disabled:text-gray-400"
            placeholder="Type your answer..."
            value={inputValue}
            disabled={inputLocked}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={onKeyDown}
            aria-label="Your message"
          />
          <button
            type="button"
            disabled={inputLocked || !inputValue.trim()}
            onClick={handleSend}
            className="shrink-0 rounded-lg bg-[#5B2D8E] px-5 py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
