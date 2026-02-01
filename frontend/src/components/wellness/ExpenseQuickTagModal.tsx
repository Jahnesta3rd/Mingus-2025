import React, { useState, useCallback, useEffect, useRef } from 'react';
import { X, Check, ShoppingBag, UtensilsCrossed, Film, Car, Home, CreditCard } from 'lucide-react';
import { TriggerPillButton, type TriggerValue } from './TriggerPillButton';
import { MoodButton, type MoodValue } from './MoodButton';
import type { ExpenseMoodTag } from '../../hooks/useExpenseTagging';

export interface Expense {
  id: string;
  amount: number;
  merchant: string;
  category: string;
  date: string;
}

const TRIGGERS: Array<{ value: TriggerValue; label: string }> = [
  { value: 'planned', label: 'Planned' },
  { value: 'needed', label: 'Needed' },
  { value: 'impulse', label: 'Impulse' },
  { value: 'treat', label: 'Treat' },
  { value: 'stressed', label: 'Stressed' },
  { value: 'bored', label: 'Bored' },
];

const MOODS: Array<{ value: MoodValue; emoji: string; label: string }> = [
  { value: 'great', emoji: '😊', label: 'Great' },
  { value: 'okay', emoji: '😐', label: 'Okay' },
  { value: 'meh', emoji: '😬', label: 'Meh' },
];

function CategoryIcon({ category }: { category: string }) {
  const c = category.toLowerCase();
  if (c.includes('food') || c.includes('dining') || c.includes('grocery')) return <UtensilsCrossed className="w-5 h-5" aria-hidden />;
  if (c.includes('entertainment') || c.includes('movie')) return <Film className="w-5 h-5" aria-hidden />;
  if (c.includes('transport') || c.includes('gas') || c.includes('car')) return <Car className="w-5 h-5" aria-hidden />;
  if (c.includes('home') || c.includes('rent') || c.includes('utility')) return <Home className="w-5 h-5" aria-hidden />;
  if (c.includes('shopping') || c.includes('retail')) return <ShoppingBag className="w-5 h-5" aria-hidden />;
  return <CreditCard className="w-5 h-5" aria-hidden />;
}

export interface ExpenseQuickTagModalProps {
  expense: Expense;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (tag: ExpenseMoodTag) => void;
  onSkip: () => void;
  className?: string;
}

/**
 * Modal for quick expense tagging: trigger (why) + mood (how you feel).
 * Bottom sheet on mobile, centered on desktop. ESC / backdrop close.
 */
export const ExpenseQuickTagModal: React.FC<ExpenseQuickTagModalProps> = ({
  expense,
  isOpen,
  onClose,
  onSubmit,
  onSkip,
  className = '',
}) => {
  const [trigger, setTrigger] = useState<TriggerValue | null>(null);
  const [mood_after, setMoodAfter] = useState<MoodValue | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  const reset = useCallback(() => {
    setTrigger(null);
    setMoodAfter(null);
    setSaving(false);
    setSuccess(false);
  }, []);

  useEffect(() => {
    if (!isOpen) reset();
  }, [isOpen, reset]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onSkip();
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onSkip, onClose]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onSkip();
        onClose();
      }
    },
    [onSkip, onClose]
  );

  const handleSkip = useCallback(() => {
    onSkip();
    onClose();
  }, [onSkip, onClose]);

  const handleSave = useCallback(async () => {
    if (trigger === null || mood_after === null) return;
    setSaving(true);
    try {
      onSubmit({ expense_id: expense.id, trigger, mood_after });
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 600);
    } catch {
      setSaving(false);
    }
  }, [expense.id, trigger, mood_after, onSubmit, onClose]);

  const canSave = trigger !== null && mood_after !== null;

  if (!isOpen) return null;

  const amountStr = typeof expense.amount === 'number'
    ? expense.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 })
    : `$${expense.amount}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="expense-quick-tag-title"
      aria-describedby="expense-quick-tag-desc"
    >
      <div
        className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm animate-fade-in"
        onClick={handleBackdropClick}
        onKeyDown={(e) => e.key === 'Escape' && handleSkip()}
        aria-hidden
      />
      <div
        ref={modalRef}
        className={`
          relative w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl
          bg-slate-800 border border-slate-700 shadow-xl
          max-h-[90vh] overflow-y-auto
          animate-slide-up-sheet sm:animate-scale-in
          ${className}
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {success ? (
          <div
            className="flex flex-col items-center justify-center py-16 px-6 text-violet-400"
            role="status"
            aria-live="polite"
          >
            <Check className="w-16 h-16 mb-4 animate-scale-in" aria-hidden />
            <p className="text-lg font-semibold text-slate-100">Tag saved!</p>
          </div>
        ) : (
          <>
            <div className="sticky top-0 flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800 z-10">
              <h2 id="expense-quick-tag-title" className="text-lg font-bold text-slate-100">
                Quick tag? 🏷️
              </h2>
              <button
                type="button"
                onClick={handleSkip}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500"
                aria-label="Close and skip"
              >
                <X className="w-5 h-5" aria-hidden />
              </button>
            </div>

            <div id="expense-quick-tag-desc" className="p-4 space-y-6">
              <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-700/50 border border-slate-600">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-violet-500/20 text-violet-400 shrink-0">
                  <CategoryIcon category={expense.category} />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-slate-100 tabular-nums">
                    {amountStr} at {expense.merchant}
                  </p>
                  <p className="text-sm text-slate-400 capitalize">{expense.category}</p>
                </div>
              </div>

              <section aria-labelledby="trigger-label">
                <h3 id="trigger-label" className="text-sm font-semibold text-slate-300 mb-3">
                  Why did you buy this?
                </h3>
                <div className="grid grid-cols-3 gap-2">
                  {TRIGGERS.map(({ value, label }) => (
                    <TriggerPillButton
                      key={value}
                      value={value}
                      label={label}
                      selected={trigger === value}
                      onSelect={() => setTrigger(value)}
                      ariaLabel={`${label}${trigger === value ? ', selected' : ''}`}
                    />
                  ))}
                </div>
              </section>

              <section aria-labelledby="mood-label">
                <h3 id="mood-label" className="text-sm font-semibold text-slate-300 mb-3">
                  How do you feel about it?
                </h3>
                <div className="flex gap-3 flex-wrap">
                  {MOODS.map(({ value, emoji, label }) => (
                    <MoodButton
                      key={value}
                      value={value}
                      emoji={emoji}
                      label={label}
                      selected={mood_after === value}
                      onSelect={() => setMoodAfter(value)}
                      ariaLabel={`${emoji} ${label}${mood_after === value ? ', selected' : ''}`}
                    />
                  ))}
                </div>
              </section>
            </div>

            <div className="sticky bottom-0 flex gap-3 p-4 border-t border-slate-700 bg-slate-800">
              <button
                type="button"
                onClick={handleSkip}
                className="min-h-[48px] flex-1 rounded-xl font-semibold bg-slate-700 text-slate-200 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-800 active:scale-[0.98]"
                aria-label="Skip tagging"
              >
                Skip
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={!canSave || saving}
                className="min-h-[48px] flex-1 rounded-xl font-semibold bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-800 active:scale-[0.98] transition-transform"
                aria-label="Save tag"
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ExpenseQuickTagModal;
