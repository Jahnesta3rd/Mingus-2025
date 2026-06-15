import React, { useState } from 'react';
import { INSURANCE_GLOSSARY } from '../data/insuranceGlossary';

export interface GlossaryChipProps {
  termId: string;
  className?: string;
}

export function GlossaryChip({ termId, className = '' }: GlossaryChipProps) {
  const [expanded, setExpanded] = useState(false);
  const term = INSURANCE_GLOSSARY.find((item) => item.id === termId);

  if (!term) {
    return null;
  }

  return (
    <div className={className}>
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        className="cursor-pointer text-xs text-blue-500 underline"
        aria-expanded={expanded}
      >
        What is this? {expanded ? '▴' : '▾'}
      </button>
      {expanded ? (
        <div className="mt-1 rounded-xl border border-blue-100 bg-blue-50 p-3">
          <p className="text-xs font-semibold text-blue-800">
            {term.emoji} {term.term}
          </p>
          <p className="mt-1 text-xs text-gray-700">{term.plain_english}</p>
          <p className="mt-1.5 text-xs font-medium text-blue-700">
            💡 {term.bottom_line}
          </p>
        </div>
      ) : null}
    </div>
  );
}
