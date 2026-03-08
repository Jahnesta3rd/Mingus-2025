import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';

/**
 * Dedicated sign-up step between assessment result and checkout.
 * Email and first name pre-filled from URL params; user sets password and creates account.
 */
const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') ?? '';
  const firstName = searchParams.get('firstName') ?? '';
  const fromAssessment = searchParams.get('from') === 'assessment';
  const assessmentType = searchParams.get('type') ?? 'ai-risk';

  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email?.trim()) {
      setError('Email is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setLoading(true);
    try {
      const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
      const response = await fetch(`${apiBase}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token' },
        credentials: 'include',
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          firstName: firstName.trim() || undefined,
          first_name: firstName.trim() || undefined,
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setError(data.error || 'Registration failed. Please try again.');
        return;
      }

      if (data.token) {
        localStorage.setItem('auth_token', data.token);
      }
      const redirectUrl = fromAssessment
        ? `/checkout?from=assessment&type=${encodeURIComponent(assessmentType)}`
        : '/checkout';
      navigate(redirectUrl, { replace: true });
    } catch (err) {
      const isNetworkError = err instanceof TypeError && (err.message === 'Failed to fetch' || err.message.includes('NetworkError'));
      setError(isNetworkError ? 'Unable to reach server. Check your connection or try again later.' : (err instanceof Error ? err.message : 'Something went wrong.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="mt-2 text-gray-400 text-sm">One more step before checkout.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 bg-gray-800 rounded-xl p-6 shadow-xl border border-gray-700" aria-busy={loading} aria-describedby={error ? 'signup-error' : undefined}>
          <div>
            <label htmlFor="signup-email" className="block text-sm font-medium text-gray-300 mb-1">
              Email
            </label>
            <input
              id="signup-email"
              type="email"
              value={email}
              readOnly
              className="w-full px-4 py-2.5 rounded-lg bg-gray-700 text-gray-300 border border-gray-600 cursor-not-allowed"
              aria-readonly="true"
            />
          </div>

          <div>
            <label htmlFor="signup-firstName" className="block text-sm font-medium text-gray-300 mb-1">
              First name
            </label>
            <input
              id="signup-firstName"
              type="text"
              value={firstName}
              readOnly
              className="w-full px-4 py-2.5 rounded-lg bg-gray-700 text-gray-300 border border-gray-600 cursor-not-allowed"
              aria-readonly="true"
            />
          </div>

          <div>
            <label htmlFor="signup-password" className="block text-sm font-medium text-gray-300 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                minLength={8}
                autoComplete="new-password"
                className="w-full px-4 py-2.5 pr-12 rounded-lg bg-gray-800 text-white border border-gray-600 focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {error && (
            <div id="signup-error" className="rounded-lg bg-red-900/30 border border-red-500/50 px-4 py-3 text-red-200 text-sm" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            data-testid="signup-create-account"
            className="w-full py-3 px-4 rounded-lg font-semibold text-white bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            {loading ? 'Creating account…' : 'Create Account & Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SignupPage;
