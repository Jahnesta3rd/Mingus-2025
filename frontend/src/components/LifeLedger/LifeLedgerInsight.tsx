import React from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';

export interface LifeLedgerInsightData {
  id: string;
  module: string;
  message: string;
  action_url: string | null;
}

const MODULE_EMOJI: Record<string, string> = {
  vibe: '💑',
  body: '💪',
  roof: '🏠',
  vehicle: '🚗',
};

export interface LifeLedgerInsightProps {
  insight: LifeLedgerInsightData;
  onDismiss: (id: string) => void;
}

const LifeLedgerInsight: React.FC<LifeLedgerInsightProps> = ({ insight, onDismiss }) => {
  const emoji = MODULE_EMOJI[insight.module] ?? '💛';

  return (
    <div className="relative rounded-lg border border-gray-700/80 bg-gray-900 pl-4 pr-10 py-3 border-l-4 border-l-amber-400 shadow-sm">
      <button
        type="button"
        onClick={() => onDismiss(insight.id)}
        className="absolute top-2 right-2 p-1 rounded-md text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
        aria-label="Dismiss insight"
      >
        <X className="w-4 h-4" strokeWidth={2} />
      </button>
      <div className="flex gap-3 items-start text-left">
        <span className="text-xl flex-shrink-0 leading-none mt-0.5" aria-hidden>
          {emoji}
        </span>
        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-sm text-gray-100 leading-snug">{insight.message}</p>
          {insight.action_url ? (
            <Link
              to={insight.action_url}
              className="inline-block text-xs font-semibold text-amber-400 hover:text-amber-300 hover:underline"
            >
              Take Action
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default LifeLedgerInsight;
