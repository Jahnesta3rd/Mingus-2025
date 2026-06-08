import { useEffect, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { CHECKUPS_HUB_PATH, formatRelativeLastUpdate } from './checkupShared';
import './checkupDesignTokens.css';

export type CheckupWrapperShellProps = {
  title: string;
  /** Numeric score pill, e.g. body_score */
  score?: number | null;
  /** Alternative header pill text (e.g. "3 people tracked") */
  headerPill?: string;
  lastCompletedAt?: string | null;
  loading?: boolean;
  error?: string | null;
  successMessage?: string | null;
  children: ReactNode;
  className?: string;
};

export function CheckupWrapperShell({
  title,
  score,
  headerPill,
  lastCompletedAt,
  loading = false,
  error,
  successMessage,
  children,
  className = '',
}: CheckupWrapperShellProps) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  const relative = formatRelativeLastUpdate(lastCompletedAt);
  const pillText =
    headerPill ??
    (score != null ? `Score ${score}` : 'Not yet assessed');

  if (authLoading || !isAuthenticated) {
    return (
      <div className="dash-checkup-root flex min-h-[50vh] items-center justify-center px-4">
        <p className="text-sm" style={{ color: 'var(--ink-mid)' }}>
          Checking your session…
        </p>
      </div>
    );
  }

  return (
    <div className={`dash-checkup-root ${className}`.trim()}>
      <header
        className="px-4 py-6 sm:px-6 lg:px-8"
        style={{ background: 'var(--mingus-purple)' }}
      >
        <div className="mx-auto max-w-3xl">
          <Link
            to={CHECKUPS_HUB_PATH}
            className="inline-flex min-h-11 items-center text-sm font-semibold text-white/90 transition hover:text-white"
          >
            ← Checkups
          </Link>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="font-display text-2xl font-semibold text-white sm:text-3xl">{title}</h1>
            <span
              className="inline-flex shrink-0 items-center self-start rounded-full px-4 py-1.5 text-sm font-semibold"
              style={{ background: 'var(--mingus-purple-deep)', color: '#fff' }}
            >
              {loading ? '…' : pillText}
            </span>
          </div>
        </div>
      </header>

      <div
        className="border-b px-4 py-3 sm:px-6 lg:px-8"
        style={{ background: 'var(--whisper-purple)', borderColor: 'var(--line)' }}
      >
        <p className="mx-auto max-w-3xl text-sm" style={{ color: 'var(--ink-mid)' }}>
          {relative ? (
            <>
              Last completed: <span className="font-medium text-[var(--ink)]">{relative}</span>
            </>
          ) : (
            'First checkup.'
          )}
        </p>
      </div>

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        {successMessage ? (
          <div
            className="mb-6 rounded-xl border px-4 py-3 text-sm font-medium"
            style={{
              background: 'var(--soft-purple)',
              borderColor: 'var(--lavender-300)',
              color: 'var(--mingus-purple-deep)',
            }}
            role="status"
          >
            {successMessage}
          </div>
        ) : null}

        {error ? (
          <div
            className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
            role="alert"
          >
            {error}
          </div>
        ) : null}

        {children}
      </main>
    </div>
  );
}

export default CheckupWrapperShell;
