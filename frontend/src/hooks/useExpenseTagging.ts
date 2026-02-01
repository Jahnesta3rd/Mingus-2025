import { useState, useCallback, useEffect } from 'react';

const SKIP_STORAGE_KEY = 'mingus_expense_tag_skip_count';
const MAX_SKIPS_BEFORE_STOP = 5;

export type TriggerValue =
  | 'planned'
  | 'needed'
  | 'impulse'
  | 'treat'
  | 'stressed'
  | 'bored';

export type MoodValue = 'great' | 'okay' | 'meh';

export interface ExpenseMoodTag {
  expense_id: string;
  trigger: TriggerValue;
  mood_after: MoodValue;
}

function getStoredSkipCount(): number {
  try {
    const raw = localStorage.getItem(SKIP_STORAGE_KEY);
    return raw ? Math.max(0, parseInt(raw, 10)) : 0;
  } catch {
    return 0;
  }
}

function setStoredSkipCount(count: number): void {
  try {
    localStorage.setItem(SKIP_STORAGE_KEY, String(count));
  } catch {
    // ignore
  }
}

export interface UseExpenseTaggingOptions {
  /** Called after tag is submitted (e.g. API call) */
  onSubmit?: (tag: ExpenseMoodTag) => void | Promise<void>;
}

export interface UseExpenseTaggingReturn {
  trigger: TriggerValue | null;
  setTrigger: (v: TriggerValue | null) => void;
  mood_after: MoodValue | null;
  setMoodAfter: (v: MoodValue | null) => void;
  reset: () => void;
  submitTag: (expenseId: string) => Promise<boolean>;
  recordSkip: () => void;
  skipCount: number;
  shouldPrompt: boolean;
  resetSkipCount: () => void;
}

/**
 * Manages expense tagging state and skip count for auto-prompting.
 * After 5 skips, shouldPrompt is false so parent can stop auto-prompting.
 */
export function useExpenseTagging(
  options: UseExpenseTaggingOptions = {}
): UseExpenseTaggingReturn {
  const { onSubmit } = options;
  const [trigger, setTrigger] = useState<TriggerValue | null>(null);
  const [mood_after, setMoodAfter] = useState<MoodValue | null>(null);
  const [skipCount, setSkipCount] = useState(getStoredSkipCount);

  useEffect(() => {
    setSkipCount(getStoredSkipCount());
  }, []);

  const reset = useCallback(() => {
    setTrigger(null);
    setMoodAfter(null);
  }, []);

  const recordSkip = useCallback(() => {
    const next = getStoredSkipCount() + 1;
    setStoredSkipCount(next);
    setSkipCount(next);
  }, []);

  const resetSkipCount = useCallback(() => {
    setStoredSkipCount(0);
    setSkipCount(0);
  }, []);

  const submitTag = useCallback(
    async (expenseId: string): Promise<boolean> => {
      if (trigger === null || mood_after === null) return false;
      const tag: ExpenseMoodTag = { expense_id: expenseId, trigger, mood_after };
      try {
        await onSubmit?.(tag);
        reset();
        return true;
      } catch {
        return false;
      }
    },
    [trigger, mood_after, onSubmit, reset]
  );

  const shouldPrompt = skipCount < MAX_SKIPS_BEFORE_STOP;

  return {
    trigger,
    setTrigger,
    mood_after,
    setMoodAfter,
    reset,
    submitTag,
    recordSkip,
    skipCount,
    shouldPrompt,
    resetSkipCount,
  };
}

export default useExpenseTagging;
