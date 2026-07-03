import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import SessionSetupTerminalError from './SessionSetupTerminalError';
import BetaCodeInput from '../BetaCodeInput';

async function pingVibeMingusConverted(leadId: string | null, email: string): Promise<void> {
  const norm = email.trim().toLowerCase();
  if (!norm) return;
  try {
    const csrfRes = await fetch('/api/vibe-checkups/csrf-token', { credentials: 'include' });
    if (!csrfRes.ok) return;
    const { csrf_token } = (await csrfRes.json()) as { csrf_token?: string };
    if (!csrf_token) return;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrf_token,
    };
    const body = JSON.stringify({ email: norm });
    if (leadId) {
      await fetch(`/api/vibe-checkups/lead/${encodeURIComponent(leadId)}/mingus-converted`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body,
      });
    } else {
      await fetch('/api/vibe-checkups/lead/mingus-converted-by-email', {
        method: 'POST',
        credentials: 'include',
        headers,
        body,
      });
    }
  } catch {
    /* non-blocking */
  }
}

const RegisterPage: React.FC = () => {
  const { register, loading, isAuthenticated, awaitSessionReady } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loveLedger = searchParams.get('source') === 'love_ledger';
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [registrationBeta, setRegistrationBeta] = useState(false);
  const [betaCode, setBetaCode] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [sessionSetupPending, setSessionSetupPending] = useState(false);
  const [sessionSetupError, setSessionSetupError] = useState(false);
  const postRegisterNavigatedRef = useRef(false);
  const fromAssessment = searchParams.get('from') === 'assessment';
  const assessmentIdParam = searchParams.get('assessment_id');
  const assessmentTokenParam = searchParams.get('token');

  useEffect(() => {
    if (!fromAssessment) return;
    const emailParam = searchParams.get('email');
    if (emailParam) {
      setFormData((prev) => ({ ...prev, email: emailParam }));
    }
  }, [fromAssessment, searchParams]);

  useEffect(() => {
    if (
      !loading &&
      isAuthenticated &&
      !success &&
      !isRegistering &&
      !sessionSetupPending &&
      !sessionSetupError
    ) {
      navigate('/welcome', { replace: true });
    }
  }, [
    loading,
    isAuthenticated,
    success,
    isRegistering,
    sessionSetupPending,
    sessionSetupError,
    navigate,
  ]);

  useEffect(() => {
    if (!success || postRegisterNavigatedRef.current) return;

    let cancelled = false;
    setSessionSetupPending(true);
    setSessionSetupError(false);

    (async () => {
      try {
        await awaitSessionReady();
        if (cancelled) return;
        postRegisterNavigatedRef.current = true;
        navigate('/welcome', { replace: true });
      } catch {
        if (!cancelled) {
          setSessionSetupError(true);
        }
      } finally {
        if (!cancelled) {
          setSessionSetupPending(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [success, navigate, awaitSessionReady]);

  const handleSessionSetupRetry = useCallback(async () => {
    setSessionSetupError(false);
    setSessionSetupPending(true);
    try {
      await awaitSessionReady();
      postRegisterNavigatedRef.current = true;
      navigate('/welcome', { replace: true });
    } catch {
      setSessionSetupError(true);
    } finally {
      setSessionSetupPending(false);
    }
  }, [awaitSessionReady, navigate]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleBetaCode = useCallback((code: string) => {
    setBetaCode(code);
  }, []);

  const handleBetaClear = useCallback(() => {
    setBetaCode(null);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!betaCode) {
      setError('A beta invite code is required to register.');
      return;
    }

    setIsRegistering(true);
    try {
      const vcLeadParam = loveLedger ? searchParams.get('vc_lead_id') : null;
      const { isBeta } = await register(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName,
        {
          beta_code: betaCode,
          ...(loveLedger && vcLeadParam ? { vc_lead_id: vcLeadParam } : {}),
          ...(fromAssessment && assessmentIdParam
            ? { assessment_id: assessmentIdParam }
            : {}),
          ...(fromAssessment && assessmentTokenParam
            ? { token: assessmentTokenParam }
            : {}),
        }
      );
      if (loveLedger) {
        void pingVibeMingusConverted(vcLeadParam, formData.email);
        try {
          sessionStorage.setItem('mingus_vc_import_pending', '1');
          sessionStorage.setItem(
            'mingus_vc_import_had_lead',
            vcLeadParam ? '1' : '0'
          );
        } catch {
          /* ignore */
        }
      }
      setRegistrationBeta(isBeta);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setIsRegistering(false);
    }
  };

  if (success) {
    if (sessionSetupError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
          <SessionSetupTerminalError onRetry={() => void handleSessionSetupRetry()} />
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <div className="rounded-md bg-green-50 p-6 max-w-md border border-green-200 shadow-sm">
          {registrationBeta ? (
            <>
              <h3 className="text-base font-semibold text-green-900">Welcome to the Mingus Beta!</h3>
              <p className="mt-3 text-sm text-green-800 leading-relaxed">
                You have been granted full Professional access. Your feedback helps shape the future of
                Mingus.
              </p>
              <p className="mt-4 text-xs text-green-700">
                {sessionSetupPending ? 'Setting up your account…' : 'Taking you to your welcome…'}
              </p>
            </>
          ) : (
            <>
              <h3 className="text-sm font-medium text-green-800">Account created successfully!</h3>
              <p className="mt-2 text-sm text-green-700">Taking you to your welcome…</p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen bg-gray-50 flex justify-center py-12 px-4 sm:px-6 lg:px-8 ${
        loveLedger ? 'items-start' : 'items-center'
      }`}
    >
      <div
        className={`w-full min-w-0 space-y-8 ${loveLedger ? 'max-w-4xl' : 'max-w-md'}`}
      >
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center">
            <img src="/mingus-logo.png" alt="Mingus" className="h-12 w-auto object-contain" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start your journey to financial wellness
          </p>
        </div>
        {loveLedger && (
          <div
            className="rounded-lg border border-amber-200/80 bg-amber-50/90 px-4 py-3 text-center text-sm text-amber-950 shadow-sm break-words"
            role="status"
          >
            Welcome from Vibe Checkups 💛 Your email is pre-filled.
          </div>
        )}

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3">
          <p className="text-sm font-medium text-gray-800">
            Have a beta invite code? Enter it here to get free Professional access.
          </p>
          <BetaCodeInput onValidCode={handleBetaCode} onClear={handleBetaClear} />
        </div>

        {betaCode && (
          <form className="mt-8 space-y-6 min-w-0" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm space-y-4">
              <div>
                <label htmlFor="firstName" className="sr-only">
                  First name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  autoComplete="given-name"
                  required
                  className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm"
                  placeholder="First name"
                  value={formData.firstName}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="lastName" className="sr-only">
                  Last name
                </label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  autoComplete="family-name"
                  className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm"
                  placeholder="Last name"
                  value={formData.lastName}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="email" className="sr-only">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm"
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm"
                  placeholder="Password (min 8 characters)"
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="rounded-lg border border-violet-200 bg-violet-50 px-4 py-3 text-sm text-violet-900">
              You are registering as a Beta user with full Professional access. No payment required.
            </div>

            {error && <div className="text-red-600 text-sm text-center">{error}</div>}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-violet-600 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400 disabled:opacity-50"
              >
                {loading ? 'Creating account...' : 'Sign up'}
              </button>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link to="/login" className="font-medium text-violet-600 hover:text-violet-500">
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default RegisterPage;
