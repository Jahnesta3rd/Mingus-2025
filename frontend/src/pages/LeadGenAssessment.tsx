import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

/**
 * Public-facing assessment page for unauthenticated lead capture.
 * Maps ?type=vibe|body|roof|vehicle to the appropriate assessment flow.
 * On completion → email capture → signup.
 */
export const LeadGenAssessment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const assessmentType = searchParams.get('type') || 'vibe';
  const source = searchParams.get('source') || 'marketing';

  const [showEmailCapture, setShowEmailCapture] = useState(false);
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const getAssessmentContent = () => {
    switch (assessmentType) {
      case 'body':
        return (
          <div>
            <h2>Body & Wellness Check</h2>
            <p>Quick assessment of your physical wellness and activity level.</p>
            <button type="button" onClick={() => navigate('/body-check')}>
              Start Assessment
            </button>
            <button
              type="button"
              onClick={() => setShowEmailCapture(true)}
              style={{ marginLeft: '10px' }}
            >
              Skip and Sign Up
            </button>
          </div>
        );
      case 'roof':
        return (
          <div>
            <h2>Housing & Roof Check</h2>
            <p>Let&apos;s understand your housing situation and needs.</p>
            <button type="button" onClick={() => navigate('/roof-check')}>
              Start Assessment
            </button>
            <button
              type="button"
              onClick={() => setShowEmailCapture(true)}
              style={{ marginLeft: '10px' }}
            >
              Skip and Sign Up
            </button>
          </div>
        );
      case 'vehicle':
        return (
          <div>
            <h2>Vehicle Cost Analysis</h2>
            <p>Understand your vehicle expenses and maintenance needs.</p>
            <button type="button" onClick={() => navigate('/vehicle-check')}>
              Start Assessment
            </button>
            <button
              type="button"
              onClick={() => setShowEmailCapture(true)}
              style={{ marginLeft: '10px' }}
            >
              Skip and Sign Up
            </button>
          </div>
        );
      case 'vibe':
      default:
        return (
          <div>
            <h2>Your Vibe & Relationships</h2>
            <p>Quick check-in on your emotional state and relationships.</p>
            <button type="button" onClick={() => navigate('/vibe-checkups')}>
              Start Assessment
            </button>
            <button
              type="button"
              onClick={() => setShowEmailCapture(true)}
              style={{ marginLeft: '10px' }}
            >
              Skip and Sign Up
            </button>
          </div>
        );
    }
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    fetch('/api/assessments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        assessment_type: assessmentType,
        source,
        skipped: true,
      }),
    })
      .then(() => {
        setSubmitted(true);
        navigate(
          `/register?email=${encodeURIComponent(email)}&from=assessment&type=${assessmentType}`
        );
      })
      .catch((err) => {
        console.error('Lead capture failed:', err);
        navigate(`/register?email=${encodeURIComponent(email)}`);
      });
  };

  if (submitted) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <h2>Thanks for your interest!</h2>
        <p>Redirecting to sign up...</p>
      </div>
    );
  }

  if (showEmailCapture) {
    return (
      <div style={{ maxWidth: '400px', margin: '40px auto', padding: '20px' }}>
        <h2>Create Your Account</h2>
        <p>Join Mingus to get personalized financial wellness insights.</p>
        <form onSubmit={handleEmailSubmit}>
          <input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
          />
          <button type="submit" style={{ width: '100%', padding: '10px' }}>
            Sign Up
          </button>
          <button
            type="button"
            onClick={() => setShowEmailCapture(false)}
            style={{
              width: '100%',
              padding: '10px',
              marginTop: '10px',
              background: '#f0f0f0',
            }}
          >
            Back to Assessment
          </button>
        </form>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', margin: '40px auto', padding: '20px' }}>
      {getAssessmentContent()}
    </div>
  );
};
