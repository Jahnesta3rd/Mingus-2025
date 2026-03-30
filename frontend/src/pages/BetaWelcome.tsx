import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';

/** Ensures token exists; unauthenticated users go to /beta (not /login). */
const BetaWelcomeGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/beta', { replace: true });
      return;
    }
    setAllowed(true);
  }, [navigate]);

  if (allowed !== true) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }
  return <>{children}</>;
};

const BetaWelcomeContent: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const res = await fetch('/api/profile/setup-status', { credentials: 'include' });
        if (!res.ok) {
          navigate('/beta', { replace: true });
          return;
        }
        const data = (await res.json()) as { is_beta?: boolean; data?: { is_beta?: boolean } };
        const isBeta = data.is_beta === true || data.data?.is_beta === true;
        if (cancelled) return;
        if (!isBeta) {
          navigate('/dashboard', { replace: true });
          return;
        }
        setChecked(true);
      } catch {
        if (!cancelled) navigate('/beta', { replace: true });
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  const firstName = (user?.name || 'there').trim() || 'there';

  if (!checked) {
    return <LoadingSpinner fullScreen message="Confirming your beta access…" />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl p-8 space-y-6 text-center">
        <div className="flex justify-center">
          <CheckCircle2 className="h-16 w-16 text-green-600" aria-hidden />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome to the Mingus Beta, {firstName}!</h1>
        <p className="text-sm text-gray-600 leading-relaxed text-left">
          Your Professional tier access is active. Here is what you can do: explore all features, complete your
          financial profile, and share your honest feedback with us — it directly shapes what gets built next.
        </p>
        <ul className="text-left text-sm text-gray-700 space-y-2 list-disc pl-5">
          <li>Wellness-Finance Correlation</li>
          <li>Vehicle Analytics</li>
          <li>Advanced Housing Intelligence</li>
        </ul>
        <div className="flex flex-col gap-3 pt-2">
          <Link
            to="/dashboard"
            className="inline-flex justify-center rounded-lg py-3 px-4 text-sm font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500"
            style={{ backgroundColor: '#5B2D8E' }}
          >
            Take Me to My Dashboard
          </Link>
          <Link to="/profile/setup" className="text-sm text-violet-700 hover:text-violet-900 font-medium">
            Complete Your Profile First
          </Link>
        </div>
      </div>
    </div>
  );
};

const BetaWelcome: React.FC = () => (
  <BetaWelcomeGate>
    <BetaWelcomeContent />
  </BetaWelcomeGate>
);

export default BetaWelcome;
