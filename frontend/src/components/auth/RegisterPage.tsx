import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import BetaCodeInput from '../BetaCodeInput';
import { TierSelectionStep, type TierOption } from '../../pages/CheckoutPage';

const RegisterPage: React.FC = () => {
  const { register, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
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
  const [selectedTier, setSelectedTier] = useState<TierOption | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated && !success && !isRegistering) {
      navigate('/welcome', { replace: true });
    }
  }, [loading, isAuthenticated, success, isRegistering, navigate]);

  useEffect(() => {
    if (!success) return;
    if (registrationBeta) {
      const t = window.setTimeout(() => navigate('/welcome', { replace: true }), 4000);
      return () => window.clearTimeout(t);
    }
    if (selectedTier && selectedTier.id !== 'budget') {
      const t = window.setTimeout(() => navigate('/checkout', { replace: true }), 2000);
      return () => window.clearTimeout(t);
    }
    const t = window.setTimeout(() => navigate('/welcome', { replace: true }), 2000);
    return () => window.clearTimeout(t);
  }, [success, registrationBeta, selectedTier, navigate]);

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

    if (!betaCode && !selectedTier) {
      setError('Please choose a plan or verify a beta invite code.');
      return;
    }

    setIsRegistering(true);
    try {
      const { isBeta } = await register(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName,
        {
          beta_code: betaCode,
          selected_tier: betaCode ? 'professional' : selectedTier?.id ?? null,
        }
      );
      setRegistrationBeta(isBeta);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setIsRegistering(false);
    }
  };

  if (success) {
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
              <p className="mt-4 text-xs text-green-700">Taking you to your dashboard…</p>
            </>
          ) : (
            <>
              <h3 className="text-sm font-medium text-green-800">Account created successfully!</h3>
              <p className="mt-2 text-sm text-green-700">
                {selectedTier && selectedTier.id !== 'budget'
                  ? 'Redirecting to checkout…'
                  : 'Redirecting to welcome…'}
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
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
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
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

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3">
            <p className="text-sm font-medium text-gray-800">
              Have a beta invite code? Enter it here to get free Professional access.
            </p>
            <BetaCodeInput onValidCode={handleBetaCode} onClear={handleBetaClear} />
          </div>

          {betaCode ? (
            <div className="rounded-lg border border-violet-200 bg-violet-50 px-4 py-3 text-sm text-violet-900">
              You are registering as a Beta user with full Professional access. No payment required.
            </div>
          ) : (
            <TierSelectionStep
              selectedTier={selectedTier}
              onSelectTier={setSelectedTier}
              onContinue={() => {}}
              loading={loading}
              hideContinue
            />
          )}

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
      </div>
    </div>
  );
};

export default RegisterPage;
