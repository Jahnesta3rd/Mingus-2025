import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const ResetPasswordPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [token, setToken] = useState<string>('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const t = params.get('token') || '';
    setToken(t);
  }, [location.search]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Invalid or missing reset token. Please request a new link.');
      return;
    }

    if (!password || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ token, password }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.error || data.message || 'Failed to reset password');
      }

      setIsSuccess(true);

      // Optionally redirect to login after a short delay
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 2500);
    } catch (err: any) {
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasToken = !!token;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center">
            <img
              src="/mingus-logo.png"
              alt="Mingus"
              className="h-12 w-auto object-contain"
            />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Set a New Password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {hasToken
              ? 'Choose a strong new password for your account.'
              : 'This reset link is invalid or expired. Please request a new one.'}
          </p>
        </div>

        {isSuccess ? (
          <div className="rounded-md bg-green-50 p-4 border border-green-200">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  Password updated
                </h3>
                <p className="mt-2 text-sm text-green-700">
                  Your password has been reset successfully. Redirecting you to login...
                </p>
              </div>
            </div>
            <div className="mt-4 text-center">
              <Link
                to="/login"
                className="text-sm font-medium text-violet-600 hover:text-violet-500"
              >
                Go to login
              </Link>
            </div>
          </div>
        ) : hasToken ? (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label htmlFor="password" className="sr-only">
                  New password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                  placeholder="New password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="confirmPassword" className="sr-only">
                  Confirm new password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Updating...' : 'Update Password'}
              </button>
            </div>

            <div className="text-center">
              <Link
                to="/login"
                className="text-sm font-medium text-violet-600 hover:text-violet-500"
              >
                Back to login
              </Link>
            </div>
          </form>
        ) : (
          <div className="mt-8 space-y-4">
            <div className="text-red-600 text-sm text-center">
              This password reset link is invalid or has expired.
            </div>
            <div className="text-center">
              <Link
                to="/forgot-password"
                className="text-sm font-medium text-violet-600 hover:text-violet-500"
              >
                Request a new reset link
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResetPasswordPage;

