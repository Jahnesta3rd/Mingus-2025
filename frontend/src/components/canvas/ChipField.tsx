import { useCallback, useEffect, useMemo, useState, type KeyboardEvent } from 'react';
import { CheckCircle2 } from 'lucide-react';
import type {
  ChipOption,
  CommitFieldResponse,
  InputMode,
} from '../../types/modularOnboarding';
import { MIN_VEHICLE_YEAR, MAX_VEHICLE_YEAR } from '../../types/modularOnboarding';

export interface ChipFieldProps {
  label: string;
  value: unknown;
  fieldPath: string;
  inputMode: InputMode;
  onCommit: (
    fieldPath: string,
    value: unknown
  ) => Promise<CommitFieldResponse | undefined>;
  chips?: ChipOption[];
  min?: number;
  max?: number;
  maxLength?: number;
  hint?: string;
  /** When set, empty currency/number shows this instead of "Tap to set". */
  emptyPlaceholder?: string;
}

function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatValue(
  value: unknown,
  inputMode: InputMode,
  chips?: ChipOption[],
  emptyPlaceholder: string
): string {
  const empty = emptyPlaceholder;
  if (inputMode === 'currency') {
    if (value == null || value === '') return empty;
    const n = typeof value === 'number' ? value : Number(value);
    if (!Number.isFinite(n)) return empty;
    return `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }
  if (inputMode === 'number' || inputMode === 'year') {
    if (value == null || value === '') return empty;
    return String(value);
  }
  if (inputMode === 'date') {
    if (value == null || value === '') return empty;
    return String(value);
  }
  if (inputMode === 'chip_select') {
    if (value == null || value === '') return empty;
    const key = typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value);
    const hit = chips?.find((c) => c.value === key);
    return hit?.label ?? key;
  }
  if (inputMode === 'chip_multi') {
    if (value == null || value === '') return empty;
    const parts = String(value)
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!parts.length) return empty;
    return parts
      .map((p) => chips?.find((c) => c.value === p)?.label ?? p)
      .join(', ');
  }
  if (inputMode === 'text' || inputMode === 'zip') {
    if (value == null || value === '') return empty;
    return String(value);
  }
  return value == null || value === '' ? empty : String(value);
}

function parseCommitValue(inputMode: InputMode, raw: string): unknown {
  if (inputMode === 'currency' || inputMode === 'number' || inputMode === 'year') {
    const t = raw.trim();
    if (t === '') return null;
    const n = inputMode === 'year' ? parseInt(t, 10) : parseFloat(t);
    return Number.isFinite(n) ? n : null;
  }
  if (inputMode === 'date') {
    return raw.trim() === '' ? null : raw;
  }
  if (inputMode === 'zip') {
    return raw.trim();
  }
  if (inputMode === 'text') {
    return raw;
  }
  if (inputMode === 'chip_multi') {
    return raw;
  }
  if (inputMode === 'chip_select') {
    return raw;
  }
  return raw;
}

function errorReason(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'body' in err) {
    const b = (err as { body?: unknown }).body;
    if (b && typeof b === 'object' && 'reason' in b) {
      const r = (b as { reason?: unknown }).reason;
      if (typeof r === 'string') return r;
    }
  }
  return err instanceof Error ? err.message : fallback;
}

export function ChipField({
  label,
  value,
  fieldPath,
  inputMode,
  onCommit,
  chips,
  min,
  max,
  maxLength,
  hint,
  emptyPlaceholder = 'Tap to set',
}: ChipFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [justCommitted, setJustCommitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [multiSelected, setMultiSelected] = useState<Set<string>>(() => new Set());

  const display = useMemo(
    () => formatValue(value, inputMode, chips, emptyPlaceholder),
    [value, inputMode, chips, emptyPlaceholder]
  );

  const ariaLabel = `${label}: ${display}`;

  useEffect(() => {
    if (!isEditing || inputMode !== 'chip_multi') return;
    if (typeof value === 'string') {
      setMultiSelected(
        new Set(value.split(',').map((s) => s.trim()).filter(Boolean))
      );
    } else {
      setMultiSelected(new Set());
    }
  }, [isEditing, inputMode, value]);

  const commit = useCallback(
    async (newValue: unknown) => {
      if (newValue === value) {
        setIsEditing(false);
        return;
      }
      setIsCommitting(true);
      try {
        await onCommit(fieldPath, newValue);
        setJustCommitted(true);
        setTimeout(() => setJustCommitted(false), 1000);
        setError(null);
      } catch (err) {
        setError(errorReason(err, 'Save failed'));
      } finally {
        setIsCommitting(false);
        setIsEditing(false);
      }
    },
    [fieldPath, onCommit, value]
  );

  const enterToCommit = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        (e.target as HTMLInputElement).blur();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setIsEditing(false);
        setError(null);
      }
    },
    []
  );

  const commitMulti = useCallback(async () => {
    const joined = [...multiSelected].sort().join(',');
    await commit(joined === '' ? null : joined);
  }, [commit, multiSelected]);

  useEffect(() => {
    if (!isEditing || inputMode !== 'chip_multi') return;
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        void commitMulti();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setIsEditing(false);
        setError(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isEditing, inputMode, commitMulti]);

  const yearMin = min ?? MIN_VEHICLE_YEAR;
  const yearMax = max ?? MAX_VEHICLE_YEAR;

  const borderClass = error
    ? 'border-[#DC2626]'
    : justCommitted
      ? 'border-[#fbbf24]'
      : 'border-slate-200';

  if (isEditing) {
    if (inputMode === 'chip_select' && chips?.length) {
      return (
        <div
          className={`rounded-xl border px-3 py-2 min-h-[60px] bg-white ${borderClass}`}
        >
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {chips.map((c) => {
              const cur =
                value === true || value === false
                  ? value
                    ? 'true'
                    : 'false'
                  : value == null
                    ? ''
                    : String(value);
              const selected = cur === c.value;
              return (
                <button
                  key={c.value}
                  type="button"
                  disabled={isCommitting}
                  onClick={() => void commit(c.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                    selected
                      ? 'border-[#5B2D8E] bg-[#5B2D8E] text-[#f5f3ff]'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-[#5B2D8E]/50'
                  }`}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
          {justCommitted && (
            <CheckCircle2
              className="mt-1 h-4 w-4 text-[#fbbf24]"
              aria-hidden
            />
          )}
        </div>
      );
    }

    if (inputMode === 'chip_multi' && chips?.length) {
      return (
        <div
          className={`rounded-xl border px-3 py-2 min-h-[60px] bg-white ${borderClass}`}
        >
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {chips.map((c) => {
              const selected = multiSelected.has(c.value);
              return (
                <button
                  key={c.value}
                  type="button"
                  disabled={isCommitting}
                  onClick={() => {
                    setMultiSelected((prev) => {
                      const next = new Set(prev);
                      if (next.has(c.value)) next.delete(c.value);
                      else next.add(c.value);
                      return next;
                    });
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                    selected
                      ? 'border-[#5B2D8E] bg-[#5B2D8E] text-[#f5f3ff]'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-[#5B2D8E]/50'
                  }`}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
          <p className="mt-1 text-[10px] text-slate-400">Enter to save, Esc to cancel</p>
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
        </div>
      );
    }

    if (inputMode === 'text' || inputMode === 'zip') {
      return (
        <div className={`rounded-xl border px-3 py-2 bg-white ${borderClass}`}>
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <input
            type={inputMode === 'zip' ? 'text' : 'text'}
            inputMode={inputMode === 'zip' ? 'numeric' : undefined}
            pattern={inputMode === 'zip' ? '\\d{5}' : undefined}
            maxLength={inputMode === 'zip' ? 5 : maxLength}
            autoFocus
            defaultValue={value == null ? '' : String(value)}
            onKeyDown={enterToCommit}
            onBlur={(e) => {
              const v = parseCommitValue(inputMode, e.target.value);
              void commit(v);
            }}
            className="mt-1 w-full border-b border-[#5B2D8E] bg-transparent px-1 py-1 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
          />
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
        </div>
      );
    }

    if (inputMode === 'date') {
      return (
        <div className={`rounded-xl border px-3 py-2 bg-white ${borderClass}`}>
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <input
            type="date"
            min={todayIso()}
            autoFocus
            defaultValue={value == null ? '' : String(value)}
            onKeyDown={enterToCommit}
            onChange={(e) => {
              const v = parseCommitValue('date', e.target.value);
              void commit(v);
            }}
            onBlur={(e) => {
              const v = parseCommitValue('date', e.target.value);
              void commit(v);
            }}
            className="mt-1 w-full border-b border-[#5B2D8E] bg-transparent px-1 py-1 text-sm outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
          />
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
        </div>
      );
    }

    if (inputMode === 'currency' || inputMode === 'number' || inputMode === 'year') {
      const isCurrency = inputMode === 'currency';
      return (
        <div className={`rounded-xl border px-3 py-2 bg-white ${borderClass}`}>
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <div className={`relative mt-1 ${isCurrency ? 'pl-4' : ''}`}>
            {isCurrency && (
              <span className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 text-sm text-slate-600">
                $
              </span>
            )}
            <input
              type="number"
              inputMode="decimal"
              min={inputMode === 'year' ? yearMin : min}
              max={inputMode === 'year' ? yearMax : max}
              autoFocus
              defaultValue={
                value == null || value === ''
                  ? ''
                  : typeof value === 'number'
                    ? value
                    : String(value)
              }
              onKeyDown={enterToCommit}
              onBlur={(e) => {
                const v = parseCommitValue(inputMode, e.target.value);
                void commit(v);
              }}
              className="w-full border-b border-[#5B2D8E] bg-transparent py-1 pl-0 pr-1 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
            />
          </div>
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
        </div>
      );
    }

    return (
      <div className={`rounded-xl border px-3 py-2 bg-white ${borderClass}`}>
        <p className="text-sm text-slate-600">Unsupported editor for this field.</p>
        <button
          type="button"
          className="mt-2 text-sm font-medium text-[#5B2D8E] underline"
          onClick={() => setIsEditing(false)}
        >
          Close
        </button>
      </div>
    );
  }

  const idleValueClass =
    value == null || value === ''
      ? 'italic text-slate-400'
      : 'text-slate-900 font-medium';

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      disabled={isCommitting}
      onClick={() => {
        setError(null);
        if (inputMode === 'chip_select' && chips?.length) {
          setIsEditing(true);
          return;
        }
        if (inputMode === 'chip_multi' && chips?.length) {
          setIsEditing(true);
          return;
        }
        setIsEditing(true);
      }}
      className={`rounded-xl border text-left px-3 py-2 min-h-[60px] bg-white transition-colors hover:border-[#5B2D8E] ${borderClass}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
            {label}
          </div>
          <div className={`text-sm mt-0.5 flex items-center gap-1 ${idleValueClass}`}>
            {justCommitted && (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-[#fbbf24]" aria-hidden />
            )}
            <span>{display}</span>
          </div>
          {hint && <div className="text-[10px] text-slate-400 mt-1">{hint}</div>}
          {error && <p className="mt-1 text-xs text-[#DC2626]">{error}</p>}
        </div>
      </div>
    </button>
  );
}
