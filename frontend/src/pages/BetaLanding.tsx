import React, { useCallback, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { BetaCodeInput } from '../components/BetaCodeInput';
import { useAuth } from '../hooks/useAuth';

const inputClass =
  'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm';

const BetaLanding: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
  const [validatedCode, setValidatedCode] = useState<string | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const onValidCode = useCallback((code: string) => {
    setValidatedCode(code);
    setStep(2);
    setError('');
  }, []);

  const onClearCode = useCallback(() => {
    setValidatedCode(null);
    setStep(1);
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!validatedCode) {
      setError('Please verify your invite code first.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register(email, password, firstName, lastName, {
        beta_code: validatedCode,
        tier: 'professional',
        is_beta: true,
      });
      navigate('/beta/welcome', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 space-y-6">
        <div className="flex justify-center">
          <img src="/mingus-logo.png" alt="Mingus" className="h-12 w-auto object-contain" />
        </div>

        {step === 1 && (
          <>
            <div className="text-center space-y-2">
              <h1 className="text-2xl font-bold text-gray-900">You&apos;ve been invited to the Mingus Beta</h1>
              <p className="text-sm text-gray-600 leading-relaxed">
                Enter your invite code to get started. As a beta tester, you&apos;ll have full Professional access
                — completely free.
              </p>
            </div>
            <BetaCodeInput onValidCode={onValidCode} onClear={onClearCode} />
            <p className="text-center text-sm text-gray-600">
              <Link to="/register" className="text-violet-700 hover:text-violet-900 font-medium underline">
                Not a beta tester? Sign up here
              </Link>
            </p>
          </>
        )}

        {step === 2 && validatedCode && (
          <>
            <div
              className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm font-medium text-green-900"
              role="status"
            >
              Beta access confirmed
            </div>

            <div className="text-center space-y-1">
              <h2 className="text-xl font-semibold text-gray-900">Create your beta account</h2>
              <p className="text-sm text-gray-600">No payment required — Professional tier is included.</p>
            </div>

            <form onSubmit={handleRegister} className="space-y-4">
              {error && (
                <p className="text-sm text-red-600" role="alert">
                  {error}
                </p>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="beta-first-name" className="block text-xs font-medium text-gray-700 mb-1">
                    First name
                  </label>
                  <input
                    id="beta-first-name"
                    name="firstName"
                    type="text"
                    autoComplete="given-name"
                    required
                    className={inputClass}
                    value={firstName}
                    onChange={(ev) => setFirstName(ev.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="beta-last-name" className="block text-xs font-medium text-gray-700 mb-1">
                    Last name
                  </label>
                  <input
                    id="beta-last-name"
                    name="lastName"
                    type="text"
                    autoComplete="family-name"
                    required
                    className={inputClass}
                    value={lastName}
                    onChange={(ev) => setLastName(ev.target.value)}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="beta-email" className="block text-xs font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  id="beta-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={inputClass}
                  value={email}
                  onChange={(ev) => setEmail(ev.target.value)}
                />
              </div>
              <div>
                <label htmlFor="beta-password" className="block text-xs font-medium text-gray-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="beta-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    className={`${inputClass} pr-10`}
                    value={password}
                    onChange={(ev) => setPassword(ev.target.value)}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-2 flex items-center text-gray-500 hover:text-gray-700"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label htmlFor="beta-confirm-password" className="block text-xs font-medium text-gray-700 mb-1">
                  Confirm password
                </label>
                <div className="relative">
                  <input
                    id="beta-confirm-password"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    className={`${inputClass} pr-10`}
                    value={confirmPassword}
                    onChange={(ev) => setConfirmPassword(ev.target.value)}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-2 flex items-center text-gray-500 hover:text-gray-700"
                    onClick={() => setShowConfirmPassword((v) => !v)}
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500"
                style={{ backgroundColor: '#5B2D8E' }}
              >
                {submitting ? 'Creating account…' : 'Create My Account'}
              </button>

              <button
                type="button"
                onClick={() => {
                  setStep(1);
                  setValidatedCode(null);
                  setError('');
                }}
                className="w-full text-center text-xs text-gray-500 hover:text-gray-700"
              >
                Use a different invite code
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default BetaLanding;
