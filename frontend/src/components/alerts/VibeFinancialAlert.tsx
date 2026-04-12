import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export interface VibeFinancialAlertData {
  id: string;
  type: string;
  severity: 'info' | 'warning';
  message: string;
  action_label: string;
  action_route: string;
}

interface VibeFinancialAlertProps {
  alert: VibeFinancialAlertData;
  onDismissed?: (id: string) => void;
}

function alertAuthHeaders(): HeadersInit {
  const token =
    localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export default function VibeFinancialAlert({ alert, onDismissed }: VibeFinancialAlertProps) {
  const navigate = useNavigate();
  const [dismissing, setDismissing] = useState(false);

  const isWarning = alert.severity === 'warning';
  const containerClass = isWarning
    ? 'border border-amber-200 bg-amber-50 text-amber-700'
    : 'border border-blue-200 bg-blue-50 text-blue-700';

  const handleDismiss = async () => {
    if (dismissing) return;
    setDismissing(true);
    try {
      const res = await fetch(`/api/alerts/${encodeURIComponent(alert.id)}/read`, {
        method: 'PATCH',
        credentials: 'include',
        headers: alertAuthHeaders(),
      });
      if (res.ok) {
        onDismissed?.(alert.id);
      }
    } catch {
      // Silently keep the card visible on failure
    } finally {
      setDismissing(false);
    }
  };

  const handleAction = () => {
    navigate(alert.action_route);
  };

  return (
    <div
      className={`relative flex flex-col gap-3 rounded-xl p-4 shadow-sm sm:flex-row sm:items-start sm:justify-between ${containerClass}`}
      role="status"
    >
      <div className="flex gap-3 pr-10 sm:pr-0">
        <span className="shrink-0 text-xl leading-none" aria-hidden>
          {isWarning ? '⚠️' : 'ℹ️'}
        </span>
        <p className="text-sm font-medium leading-relaxed">{alert.message}</p>
      </div>
      <div className="flex shrink-0 flex-col gap-2 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={handleAction}
          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-[#5B2D8E] px-4 text-sm font-medium text-white hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          {alert.action_label}
        </button>
      </div>
      <button
        type="button"
        onClick={() => void handleDismiss()}
        disabled={dismissing}
        className="absolute right-2 top-2 inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-lg leading-none hover:bg-black/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50"
        aria-label="Dismiss alert"
      >
        ×
      </button>
    </div>
  );
}
