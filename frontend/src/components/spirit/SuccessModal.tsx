import React from 'react';

export interface SuccessModalProps {
  isOpen: boolean;
  onClose: () => void;
  practiceType: string;
  practiceScore: number;
  streak: number;
}

function displayPracticeType(raw: string): string {
  const map: Record<string, string> = {
    prayer: 'Prayer',
    meditation: 'Meditation',
    gratitude: 'Gratitude',
    affirmation: 'Affirmations',
    affirmations: 'Affirmations',
  };
  const k = raw.toLowerCase();
  return map[k] || raw;
}

export const SuccessModal: React.FC<SuccessModalProps> = ({
  isOpen,
  onClose,
  practiceType,
  practiceScore,
  streak,
}) => {
  if (!isOpen) return null;

  const label = displayPracticeType(practiceType);
  const isPrayer = practiceType.toLowerCase() === 'prayer';
  const hero = isPrayer ? '🙏' : '✨';

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="spirit-success-title"
        className="w-full max-w-md rounded-2xl border-2 border-[#C4A064] bg-white p-8 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-center text-6xl" aria-hidden>
          {hero}
        </div>
        <h2 id="spirit-success-title" className="mt-4 text-center font-display text-xl font-semibold text-[#0f172a]">
          Check-In Complete
        </h2>
        <p className="mt-3 text-center text-sm leading-relaxed text-slate-600">
          Your {label} session has been logged. You are on a {streak}-day streak!
        </p>
        <p className="mt-6 text-center text-sm font-medium text-[#0f172a]">
          Practice score:{' '}
          <span className="tabular-nums text-[#C4A064]">{practiceScore.toFixed(1)}</span>
          <span className="text-slate-500"> / 10</span>
        </p>
        <button
          type="button"
          onClick={onClose}
          className="mt-8 w-full rounded-xl border-2 border-[#C4A064] bg-[#0f172a] py-3 text-sm font-semibold text-[#FFF8EC] transition hover:bg-[#1e293b]"
        >
          Continue →
        </button>
      </div>
    </div>
  );
};

export default SuccessModal;
