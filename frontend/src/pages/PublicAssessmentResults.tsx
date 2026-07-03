import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

interface AssessmentAction {
  label: string;
  link: string;
}

interface PublicAssessmentResult {
  assessment_id: number;
  assessment_type: string;
  score: number;
  risk_level: string;
  recommendations: string[];
  next_steps?: string[];
  tier_title?: string;
  actions?: AssessmentAction[];
  subscores: Record<string, unknown>;
  created_at: string;
}

const ASSESSMENT_LABELS: Record<string, string> = {
  'ai-risk': 'AI Replacement Risk',
  'income-comparison': 'Income Comparison',
  'layoff-risk': 'Layoff Risk',
  'cuffing-season': 'Cuffing Season Score',
  'vehicle-financial-health': 'Vehicle Financial Health',
};

const EXPIRED_ERRORS = new Set([
  'Invalid or expired token',
  'Invalid token or assessment not found',
]);

export function PublicAssessmentResults() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [results, setResults] = useState<PublicAssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resendEmail, setResendEmail] = useState('');
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token || !assessmentId) {
      setError('Invalid link');
      setLoading(false);
      return;
    }

    fetch(`/api/assessments/${assessmentId}/public-results?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(
            (data as { error?: string }).error || 'Invalid token or assessment not found'
          );
        }
        return data as PublicAssessmentResult;
      })
      .then((data) => {
        setResults(data);
        void fetch('/api/analytics/assessment-event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            assessment_id: Number(assessmentId),
            token,
            event_type: 'results_viewed',
          }),
        }).catch((err) => console.warn('Analytics error:', err));
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [assessmentId, searchParams]);

  const handleResend = async () => {
    if (!assessmentId || !resendEmail.trim()) return;
    setResending(true);
    setResendStatus(null);
    try {
      const res = await fetch(`/api/assessments/${assessmentId}/resend-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resendEmail.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setResendStatus('New link sent — check your email!');
      } else {
        setResendStatus((data as { error?: string }).error || 'Error resending link');
      }
    } catch {
      setResendStatus('Error resending link');
    } finally {
      setResending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC] p-8 text-center text-[#64748B]">
        Loading your results…
      </div>
    );
  }

  if (error) {
    if (EXPIRED_ERRORS.has(error) || error === 'Invalid link') {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC] p-8">
          <div className="mx-auto w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
            <h2 className="mb-4 text-2xl font-bold text-[#1E293B]">Link Expired</h2>
            <p className="mb-6 text-[#64748B]">
              Your assessment link expired or is invalid. Enter your email to get a new one.
            </p>
            <input
              type="email"
              value={resendEmail}
              onChange={(e) => setResendEmail(e.target.value)}
              placeholder="your@email.com"
              className="mb-4 w-full rounded-lg border border-[#E2E8F0] p-3 text-[#1E293B]"
            />
            <button
              type="button"
              onClick={() => void handleResend()}
              disabled={resending || !resendEmail.trim()}
              className="w-full rounded-xl bg-[#5B2D8E] py-3 font-bold text-white hover:bg-[#3B1F6E] disabled:opacity-50"
            >
              {resending ? 'Sending…' : 'Send New Link'}
            </button>
            {resendStatus ? (
              <p className={`mt-4 text-sm ${resendStatus.includes('sent') ? 'text-green-600' : 'text-red-600'}`}>
                {resendStatus}
              </p>
            ) : null}
          </div>
        </div>
      );
    }

    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC] p-8 text-center">
        <p className="text-red-600">⚠️ {error}</p>
      </div>
    );
  }

  if (!results) return null;

  const token = searchParams.get('token') ?? '';
  const assessmentLabel =
    ASSESSMENT_LABELS[results.assessment_type] ?? results.assessment_type;

  return (
    <div className="min-h-screen bg-[#F8FAFC] px-4 py-12">
      <div className="mx-auto max-w-2xl rounded-2xl bg-white p-8 shadow-lg">
        <h1 className="mb-2 text-3xl font-bold text-[#5B2D8E]">{assessmentLabel}</h1>
        <p className="mb-8 text-[#64748B]">
          Results from {new Date(results.created_at).toLocaleDateString()}
        </p>

        <div className="mb-8 rounded-xl bg-[#F3E8FF] p-6 text-center">
          <div className="text-6xl font-bold text-[#5B2D8E]">{results.score}</div>
          <div className="mt-2 text-xl text-[#1E293B]">{results.risk_level}</div>
          {results.tier_title ? (
            <p className="mt-2 text-sm font-medium text-[#5B2D8E]">{results.tier_title}</p>
          ) : null}
        </div>

        <div className="mb-8">
          <h2 className="mb-4 text-xl font-bold text-[#1E293B]">Key Insights</h2>
          <ul className="list-inside list-disc space-y-2">
            {results.recommendations?.map((rec, i) => (
              <li key={i} className="text-[#475569]">
                {rec}
              </li>
            ))}
          </ul>
        </div>

        {results.next_steps && results.next_steps.length > 0 ? (
          <div className="mb-8">
            <h2 className="mb-4 text-xl font-bold text-[#1E293B]">
              Next Steps{results.tier_title ? ` for ${results.tier_title}` : ''}
            </h2>
            <ul className="list-inside list-disc space-y-2">
              {results.next_steps.map((step, i) => (
                <li key={i} className="text-[#475569]">
                  {step}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {results.actions && results.actions.length > 0 ? (
          <div className="mb-8">
            <h2 className="mb-4 text-xl font-bold text-[#1E293B]">Recommended for You</h2>
            <div className="grid grid-cols-1 gap-3">
              {results.actions.map((action, i) => (
                <a
                  key={i}
                  href={action.link}
                  className="block rounded-lg border border-[#5B2D8E] px-4 py-3 text-center font-semibold text-[#5B2D8E] hover:bg-[#F3E8FF]"
                >
                  {action.label}
                </a>
              ))}
            </div>
          </div>
        ) : null}

        <div className="rounded-xl bg-[#F3E8FF] p-6 text-center">
          <p className="mb-4 text-[#475569]">
            Create an account to save your results and unlock personalized action plans.
          </p>
          <button
            type="button"
            onClick={() =>
              navigate(
                `/register?from=assessment&type=${encodeURIComponent(results.assessment_type)}&assessment_id=${assessmentId}&token=${encodeURIComponent(token)}`
              )
            }
            className="rounded-xl bg-[#5B2D8E] px-6 py-3 font-bold text-white hover:bg-[#3B1F6E]"
          >
            Create Free Account
          </button>
        </div>
      </div>
    </div>
  );
}
