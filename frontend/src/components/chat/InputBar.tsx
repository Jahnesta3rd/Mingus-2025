import { useCallback, useEffect, useState } from 'react';
import { MicOff } from 'lucide-react';
import type { InputSpec, OnboardingPhase } from '../../types/modularOnboarding';
import {
  MAX_VEHICLE_YEAR,
  MIN_VEHICLE_YEAR,
} from '../../types/modularOnboarding';

export interface InputBarProps {
  inputHint: InputSpec | null;
  onSend: (text: string) => Promise<void> | void;
  disabled: boolean;
  phase: OnboardingPhase;
}

type QuickPick = { label: string; value: string };

function localIsoFromDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function addDaysFromToday(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return localIsoFromDate(d);
}

function currencyQuickPicks(fieldHint?: string): QuickPick[] {
  if (fieldHint === 'monthly_takehome') {
    return [
      { label: '$2500', value: '2500' },
      { label: '$3500', value: '3500' },
      { label: '$5000', value: '5000' },
      { label: '$7500', value: '7500' },
      { label: '$10k+', value: '10000' },
    ];
  }
  if (fieldHint === 'monthly_cost') {
    return [
      { label: '$800', value: '800' },
      { label: '$1200', value: '1200' },
      { label: '$1800', value: '1800' },
      { label: '$2500', value: '2500' },
      { label: '$3500+', value: '3500' },
    ];
  }
  return [
    { label: '$50', value: '50' },
    { label: '$100', value: '100' },
    { label: '$200', value: '200' },
    { label: '$400', value: '400' },
    { label: 'None', value: '0' },
  ];
}

const YEAR_QUICK_PICKS: QuickPick[] = [
  { label: '2024', value: '2024' },
  { label: '2022', value: '2022' },
  { label: '2020', value: '2020' },
  { label: '2018', value: '2018' },
  { label: '2015 or older', value: '2015' },
];

const DATE_QUICK_PICKS: QuickPick[] = [
  { label: 'Today', value: 'today' },
  { label: 'Tomorrow', value: 'tomorrow' },
  { label: 'Next week', value: 'next_week' },
  { label: 'In 1 month', value: '1m' },
  { label: 'In 3 months', value: '3m' },
  { label: 'In 6 months', value: '6m' },
];

function resolveDateQuickValue(key: string): string {
  switch (key) {
    case 'today':
      return localIsoFromDate(new Date());
    case 'tomorrow':
      return addDaysFromToday(1);
    case 'next_week':
      return addDaysFromToday(7);
    case '1m':
      return addDaysFromToday(30);
    case '3m':
      return addDaysFromToday(90);
    case '6m':
      return addDaysFromToday(180);
    default:
      return localIsoFromDate(new Date());
  }
}

function inputSpecKey(h: InputSpec | null): string | null {
  if (!h) return null;
  return JSON.stringify({
    mode: h.mode,
    placeholder: h.placeholder,
    min: h.min,
    max: h.max,
    fieldHint: h.fieldHint,
    chips: (h.chips ?? []).map((c) => `${c.value}:${c.label}`),
  });
}

function MicSlot() {
  return (
    <button
      type="button"
      disabled
      title="Voice input — coming soon"
      className="shrink-0 rounded-full border border-slate-200 p-2 text-slate-400 cursor-not-allowed"
    >
      <MicOff size={16} aria-hidden />
    </button>
  );
}

const inputRingClass =
  'flex-1 rounded-full border border-slate-300 px-4 py-2 text-[15px] outline-none focus:border-[#5B2D8E] focus:ring-2 focus:ring-[#5B2D8E]/30';

export function InputBar({
  inputHint,
  onSend,
  disabled,
  phase,
}: InputBarProps) {
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showFreeText, setShowFreeText] = useState(false);
  const [selectedChips, setSelectedChips] = useState<string[]>([]);

  const mode = inputHint?.mode ?? 'text';
  const placeholder = inputHint?.placeholder ?? 'Type your answer...';

  const hintKey = inputSpecKey(inputHint);
  useEffect(() => {
    if (hintKey == null) return;
    setDraft('');
    setShowFreeText(false);
    setSelectedChips([]);
  }, [hintKey]);

  const handleSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;
      setIsSending(true);
      try {
        await onSend(trimmed);
        setDraft('');
        setSelectedChips([]);
        setShowFreeText(false);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, onSend]
  );

  const currencyPicks =
    mode === 'currency' ? currencyQuickPicks(inputHint?.fieldHint) : null;

  if (disabled) {
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="text-center text-sm text-slate-500 py-2">
          {phase === 'committing'
            ? 'Saving...'
            : phase === 'hard_cap'
              ? 'Session complete — continue on your dashboard.'
              : phase === 'complete'
                ? 'All done!'
                : 'Disabled'}
        </div>
      </div>
    );
  }

  if (mode === 'chip_multi') {
    const chips = inputHint?.chips ?? [];
    const sortedJoin = [...selectedChips].sort().join(',');
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex gap-2 flex-wrap">
          {chips.map((chip) => {
            const on = selectedChips.includes(chip.value);
            return (
              <button
                key={chip.value}
                type="button"
                onClick={() => {
                  setSelectedChips((prev) =>
                    prev.includes(chip.value)
                      ? prev.filter((v) => v !== chip.value)
                      : [...prev, chip.value]
                  );
                }}
                className={`px-4 py-2 rounded-full border text-sm ${
                  on
                    ? 'bg-[#5B2D8E] text-white border-[#5B2D8E]'
                    : 'bg-white text-slate-700 border-slate-300 hover:border-[#5B2D8E]'
                }`}
              >
                {chip.label}
              </button>
            );
          })}
        </div>
        <button
          type="button"
          onClick={() => void handleSend(sortedJoin)}
          disabled={!sortedJoin || isSending}
          className="mt-2 w-full rounded-full bg-[#5B2D8E] py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    );
  }

  if (mode === 'chip_select') {
    const chips = inputHint?.chips ?? [];
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex gap-2 flex-wrap">
          {chips.map((chip) => (
            <button
              key={chip.value}
              type="button"
              onClick={() => setDraft(chip.value)}
              className={`px-4 py-2 rounded-full border text-sm ${
                draft === chip.value
                  ? 'bg-[#5B2D8E] text-white border-[#5B2D8E]'
                  : 'bg-white text-slate-700 border-slate-300 hover:border-[#5B2D8E]'
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setShowFreeText(true)}
          className="text-sm text-slate-500 mt-2 hover:text-[#5B2D8E] hover:underline"
        >
          Type something else
        </button>
        {showFreeText && (
          <div className="mt-2 flex gap-2">
            <MicSlot />
            <input
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void handleSend(draft);
              }}
              disabled={isSending}
              placeholder={placeholder}
              className={`${inputRingClass} rounded-lg`}
            />
          </div>
        )}
        <button
          type="button"
          onClick={() => void handleSend(draft)}
          disabled={!draft.trim() || isSending}
          className="mt-2 w-full rounded-full bg-[#5B2D8E] py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    );
  }

  if (mode === 'date') {
    const minDate = new Date().toISOString().slice(0, 10);
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex gap-2 mb-2 overflow-x-auto pb-1">
          {DATE_QUICK_PICKS.map((qp) => (
            <button
              key={qp.label}
              type="button"
              onClick={() => setDraft(resolveDateQuickValue(qp.value))}
              className="shrink-0 px-3 py-1 rounded-full border border-slate-300 text-sm hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
            >
              {qp.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2 items-center">
          <MicSlot />
          <input
            type="date"
            value={draft}
            min={minDate}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSend(draft);
            }}
            disabled={isSending}
            className={inputRingClass}
          />
          <button
            type="button"
            onClick={() => void handleSend(draft)}
            disabled={isSending || !draft.trim()}
            className="rounded-full bg-[#5B2D8E] px-6 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50 shrink-0"
          >
            Send
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'year') {
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex gap-2 mb-2 overflow-x-auto pb-1">
          {YEAR_QUICK_PICKS.map((qp) => (
            <button
              key={qp.label}
              type="button"
              onClick={() => setDraft(qp.value)}
              className="shrink-0 px-3 py-1 rounded-full border border-slate-300 text-sm hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
            >
              {qp.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2 items-center">
          <MicSlot />
          <input
            type="number"
            inputMode="numeric"
            min={inputHint?.min ?? MIN_VEHICLE_YEAR}
            max={inputHint?.max ?? MAX_VEHICLE_YEAR}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSend(draft);
            }}
            placeholder="2020"
            disabled={isSending}
            className={inputRingClass}
          />
          <button
            type="button"
            onClick={() => void handleSend(draft)}
            disabled={isSending || !draft.trim()}
            className="rounded-full bg-[#5B2D8E] px-6 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50 shrink-0"
          >
            Send
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'zip') {
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex gap-2">
          <MicSlot />
          <input
            type="text"
            inputMode="numeric"
            pattern="\d{5}"
            maxLength={5}
            value={draft}
            onChange={(e) =>
              setDraft(e.target.value.replace(/\D/g, '').slice(0, 5))
            }
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSend(draft);
            }}
            placeholder="90210"
            disabled={isSending}
            className={inputRingClass}
          />
          <button
            type="button"
            onClick={() => void handleSend(draft)}
            disabled={isSending || !draft.trim()}
            className="rounded-full bg-[#5B2D8E] px-6 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'number' || mode === 'currency') {
    return (
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        {currencyPicks && (
          <div className="flex gap-2 mb-2 overflow-x-auto pb-1">
            {currencyPicks.map((qp) => (
              <button
                key={qp.label}
                type="button"
                onClick={() => setDraft(qp.value)}
                className="shrink-0 px-3 py-1 rounded-full border border-slate-300 text-sm hover:border-[#5B2D8E] hover:text-[#5B2D8E]"
              >
                {qp.label}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2 items-center">
          <MicSlot />
          {mode === 'currency' && (
            <span className="self-center text-slate-500">$</span>
          )}
          <input
            type="number"
            inputMode="decimal"
            min={inputHint?.min}
            max={inputHint?.max}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSend(draft);
            }}
            placeholder={placeholder}
            disabled={isSending}
            className={inputRingClass}
          />
          <button
            type="button"
            onClick={() => void handleSend(draft)}
            disabled={isSending || !draft.trim()}
            className="rounded-full bg-[#5B2D8E] px-6 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50 shrink-0"
          >
            Send
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3">
      <div className="flex gap-2">
        <MicSlot />
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void handleSend(draft);
          }}
          placeholder={placeholder}
          disabled={isSending}
          className={inputRingClass}
        />
        <button
          type="button"
          onClick={() => void handleSend(draft)}
          disabled={isSending || !draft.trim()}
          className="rounded-full bg-[#5B2D8E] px-6 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
