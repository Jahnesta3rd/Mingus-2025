import React, { useCallback, useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Loader2, X } from 'lucide-react';
import {
  type MilestoneCategory,
  type MilestoneGroup,
  MILESTONE_META,
  MILESTONE_GROUPS,
  getMilestonesByGroup,
} from '../data/milestoneCategories';

export interface NewMilestoneEvent {
  id: string;
  name: string;
  category: MilestoneCategory;
  date: string;
  cost: number | null;
  notes?: string;
}

interface MilestonePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (event: NewMilestoneEvent) => Promise<void>;
  userId: string;
}

const inputClass =
  'w-full min-h-11 rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500';
const labelClass = 'mb-1.5 block text-sm font-medium text-gray-900';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function MilestonePickerModal({
  isOpen,
  onClose,
  onSave,
  userId: _userId,
}: MilestonePickerModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<MilestoneCategory | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<MilestoneGroup>>(
    () => new Set(['Family & Relationships'])
  );
  const [name, setName] = useState('');
  const [date, setDate] = useState('');
  const [cost, setCost] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setSelectedCategory(null);
    setExpandedGroups(new Set(['Family & Relationships']));
    setName('');
    setDate('');
    setCost('');
    setNotes('');
    setSaving(false);
    setSaveError(null);
  }, []);

  useEffect(() => {
    if (isOpen) reset();
  }, [isOpen, reset]);

  const toggleGroup = (group: MilestoneGroup) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) {
        next.delete(group);
      } else {
        next.add(group);
      }
      return next;
    });
  };

  const handleSelectCategory = (category: MilestoneCategory) => {
    const meta = MILESTONE_META[category];
    setSelectedCategory(category);
    setName(meta.label);
    setDate('');
    setCost(meta.defaultCost !== null ? String(meta.defaultCost) : '');
    setNotes('');
    setSaveError(null);
  };

  const handleBack = () => {
    setSelectedCategory(null);
    setSaveError(null);
  };

  const handleSave = async () => {
    if (!selectedCategory || !name.trim() || !date) return;

    setSaving(true);
    setSaveError(null);

    const parsedCost = cost.trim() ? Number.parseFloat(cost) : null;
    const event: NewMilestoneEvent = {
      id: crypto.randomUUID(),
      name: name.trim(),
      category: selectedCategory,
      date,
      cost:
        parsedCost !== null && Number.isFinite(parsedCost) ? parsedCost : null,
      ...(notes.trim() ? { notes: notes.trim() } : {}),
    };

    try {
      await onSave(event);
      onClose();
    } catch {
      setSaveError('Could not save — try again');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const selectedMeta = selectedCategory ? MILESTONE_META[selectedCategory] : null;
  const canSave = Boolean(selectedCategory && name.trim() && date && !saving);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="presentation"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div
        className="relative mx-4 flex max-h-[85vh] w-full max-w-md flex-col overflow-y-auto rounded-2xl bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="milestone-picker-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="px-5 pb-5 pt-6">
          {!selectedCategory ? (
            <>
              <h2
                id="milestone-picker-title"
                className="mb-4 pr-8 text-lg font-semibold text-gray-900"
              >
                What are you planning for?
              </h2>

              <div className="space-y-2">
                {MILESTONE_GROUPS.map((group) => {
                  const isExpanded = expandedGroups.has(group);
                  const items = getMilestonesByGroup(group);

                  return (
                    <div key={group} className="rounded-xl border border-gray-100">
                      <button
                        type="button"
                        onClick={() => toggleGroup(group)}
                        className="flex w-full items-center justify-between px-3 py-2.5 text-left text-sm font-medium text-gray-900 hover:bg-gray-50"
                        aria-expanded={isExpanded}
                      >
                        <span>{group}</span>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 shrink-0 text-gray-500" />
                        ) : (
                          <ChevronDown className="h-4 w-4 shrink-0 text-gray-500" />
                        )}
                      </button>

                      {isExpanded ? (
                        <div className="flex flex-wrap gap-2 px-3 pb-3">
                          {items.map((item) => (
                            <button
                              key={item.category}
                              type="button"
                              onClick={() => handleSelectCategory(item.category)}
                              className="rounded-full border border-gray-200 px-3 py-1.5 text-sm text-gray-800 hover:border-purple-500 hover:bg-purple-50 hover:text-purple-700"
                            >
                              {item.emoji} {item.label}
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </>
          ) : selectedMeta ? (
            <>
              <div className="mb-4 flex items-start gap-3 pr-8">
                <button
                  type="button"
                  onClick={handleBack}
                  className="mt-0.5 shrink-0 text-sm text-purple-600 hover:text-purple-800"
                >
                  ← Change
                </button>
                <h2
                  id="milestone-picker-title"
                  className="text-lg font-semibold text-gray-900"
                >
                  {selectedMeta.emoji} {selectedMeta.label}
                </h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className={labelClass} htmlFor="milestone-name">
                    What would you like to call this?
                  </label>
                  <input
                    id="milestone-name"
                    type="text"
                    className={inputClass}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className={labelClass} htmlFor="milestone-date">
                    When is it?
                  </label>
                  <input
                    id="milestone-date"
                    type="date"
                    className={inputClass}
                    value={date}
                    min={todayIso()}
                    onChange={(e) => setDate(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className={labelClass} htmlFor="milestone-cost">
                    Estimated cost (optional)
                  </label>
                  <input
                    id="milestone-cost"
                    type="number"
                    min={0}
                    step="0.01"
                    className={inputClass}
                    value={cost}
                    placeholder="$0"
                    onChange={(e) => setCost(e.target.value)}
                  />
                </div>

                <div>
                  <label className={labelClass} htmlFor="milestone-notes">
                    Notes (optional)
                  </label>
                  <textarea
                    id="milestone-notes"
                    rows={2}
                    className={inputClass}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>

                <button
                  type="button"
                  disabled={!canSave}
                  onClick={() => void handleSave()}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Saving…
                    </>
                  ) : (
                    'Add to my plan'
                  )}
                </button>

                {saveError ? (
                  <p className="text-center text-sm text-red-600" role="alert">
                    {saveError}
                  </p>
                ) : null}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default MilestonePickerModal;
