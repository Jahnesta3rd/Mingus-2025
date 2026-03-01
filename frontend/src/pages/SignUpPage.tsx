import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, loading, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState<string | null>(null);
  const [entrySource, setEntrySource] = useState<'assessment' | 'cta' | null>(null);
  const [prefilledFromAssessment, setPrefilledFromAssessment] = useState(false);

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Helper function to format assessment type
  const formatAssessmentType = (type: string): string => {
    const names: Record<string, string> = {
      'ai-risk': 'AI Replacement Risk',
      'income-comparison': 'Income Comparison',
      'cuffing-season': 'Cuffing Season Score',
      'layoff-risk': 'Layoff Risk'
    };
    return names[type] || 'Assessment';
  };

  // Pre-fill form from assessment data and set welcome message
  useEffect(() => {
    // Check entry source
    const fromAssessment = searchParams.get('from') === 'assessment';
    const fromCTA = searchParams.get('source') === 'cta';
    const assessmentType = searchParams.get('type');
    
    if (fromAssessment) {
      setEntrySource('assessment');
    } else if (fromCTA) {
      setEntrySource('cta');
    }
    
    const savedData = localStorage.getItem('mingus_assessment');
    if (savedData) {
      try {
        const { email, firstName, assessmentType: savedType } = JSON.parse(savedData);
        const hasPrefill = !!(email || firstName);
        setFormData(prev => ({
          ...prev,
          email: email || prev.email,
          firstName: firstName || prev.firstName
        }));
        if (fromAssessment && hasPrefill) {
          setPrefilledFromAssessment(true);
        }
        // Show personalized message based on entry point
        if (fromAssessment && (assessmentType || savedType)) {
          const type = assessmentType || savedType;
          setWelcomeMessage(`Complete your registration to see your full ${formatAssessmentType(type)} results!`);
        }
      } catch (e) {
        console.warn('Could not parse assessment data');
      }
    } else if (fromCTA) {
      // Show welcome message for CTA users
      setWelcomeMessage('Welcome to Mingus! Let\'s get you started on your financial wellness journey.');
    }
  }, [searchParams]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const validateForm = () => {
    if (!formData.email) {
      setError('Email is required');
      return false;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (!formData.firstName) {
      setError('First name is required');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!validateForm()) {
      return;
    }

    try {
      await register(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName
      );
      setSuccess(true);
      // Sync pre-signup assessment results to profile (assessment_results, FRI)
      try {
        await fetch('/api/assessments/sync-profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: formData.email })
        });
      } catch {
        // Non-blocking; profile may not exist yet
      }
      // Redirect to dashboard after successful registration
      // QuickSetupOverlay will appear if setup is not completed
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    }
  };

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
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start your journey to financial wellness
          </p>
          {welcomeMessage && (
            <div className="mt-4 rounded-md bg-violet-50 p-3 border border-violet-200">
              <p className="text-sm text-violet-800 text-center">{welcomeMessage}</p>
            </div>
          )}
        </div>
        
        {success ? (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  Account created successfully!
                </h3>
                <p className="mt-2 text-sm text-green-700">
                  Redirecting you to your dashboard...
                </p>
              </div>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm space-y-4">
              <div>
                <label htmlFor="firstName" className="sr-only">
                  First Name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  required
                  readOnly={prefilledFromAssessment}
                  className={`appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm ${prefilledFromAssessment ? 'bg-gray-50 cursor-not-allowed' : ''}`}
                  placeholder="First Name"
                  value={formData.firstName}
                  onChange={handleChange}
                />
                {prefilledFromAssessment && formData.firstName && (
                  <p className="text-xs text-gray-500 mt-0.5">From your assessment</p>
                )}
              </div>
              <div>
                <label htmlFor="lastName" className="sr-only">
                  Last Name
                </label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                  placeholder="Last Name (optional)"
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
                  readOnly={prefilledFromAssessment}
                  className={`appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm ${prefilledFromAssessment ? 'bg-gray-50 cursor-not-allowed' : ''}`}
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleChange}
                />
                {prefilledFromAssessment && formData.email && (
                  <p className="text-xs text-gray-500 mt-0.5">From your assessment</p>
                )}
              </div>
              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    className="appearance-none rounded-md relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                    placeholder="Password (min. 8 characters)"
                    value={formData.password}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">Must be at least 8 characters</p>
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-violet-600 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400 disabled:opacity-50"
              >
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-medium text-violet-600 hover:text-violet-500"
                >
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

export default SignUpPage;
