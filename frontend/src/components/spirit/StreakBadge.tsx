import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

export interface StreakBadgeProps {
  className?: string;
}

export const StreakBadge: React.FC<StreakBadgeProps> = ({ className = '' }) => {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [streak, setStreak] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setStreak(null);
      return;
    }
    let cancelled = false;

    const headers: Record<string, string> = { ...csrfHeaders() };
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    void (async () => {
      try {
        const res = await fetch('/api/spirit/streak', {
          credentials: 'include',
          headers,
        });
        if (!res.ok) return;
        const data = (await res.json()) as { current_streak?: number };
        if (!cancelled) setStreak(typeof data.current_streak === 'number' ? data.current_streak : 0);
      } catch {
        if (!cancelled) setStreak(0);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, getAccessToken]);

  const n = streak ?? 0;
  const active = n > 0;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border-2 px-3 py-1 text-xs font-semibold sm:text-sm ${
        active
          ? 'border-[#C4A064] bg-[#0f172a] text-[#FFF8EC]'
          : 'border-slate-300 bg-slate-100 text-slate-600'
      } ${className}`}
    >
      <span aria-hidden>🔥</span>
      {n}-Day Streak
    </span>
  );
};

export default StreakBadge;
