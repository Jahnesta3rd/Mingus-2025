import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TermsAcknowledgmentModal } from '../TermsAcknowledgment/TermsAcknowledgmentModal';
import LoadingSpinner from '../common/LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';

/**
 * After auth, ensures the user has accepted the current terms version before
 * rendering protected content.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children
 * @param {() => void} [props.onDecline] — optional; default is navigate to `/`
 */
export function TermsCheckGuard({ children, onDecline }) {
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const [hasAcceptedTerms, setHasAcceptedTerms] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryToken, setRetryToken] = useState(0);

  const fetchTermsStatus = useCallback(async () => {
    const token = getAccessToken();
    const response = await fetch('/api/user/terms-status', {
      method: 'GET',
      credentials: 'include',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      let message = `Could not load terms status (${response.status})`;
      try {
        const errJson = await response.json();
        message = errJson.error || errJson.message || message;
      } catch {
        /* ignore */
      }
      throw new Error(message);
    }

    return response.json();
  }, [getAccessToken]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchTermsStatus();
        if (cancelled) return;
        const ok =
          data.accepted === true && data.acceptedVersion === data.currentVersion;
        setHasAcceptedTerms(ok);
      } catch (e) {
        if (cancelled) return;
        setHasAcceptedTerms(null);
        setError(e instanceof Error ? e.message : 'Failed to load terms status');
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [fetchTermsStatus, retryToken]);

  const refetchAfterAccept = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchTermsStatus();
      const ok =
        data.accepted === true && data.acceptedVersion === data.currentVersion;
      setHasAcceptedTerms(ok);
    } catch (e) {
      setHasAcceptedTerms(null);
      setError(e instanceof Error ? e.message : 'Failed to verify terms acceptance');
    } finally {
      setIsLoading(false);
    }
  }, [fetchTermsStatus]);

  const handleDecline = useCallback(() => {
    if (typeof onDecline === 'function') {
      onDecline();
      return;
    }
    navigate('/', { replace: true });
  }, [navigate, onDecline]);

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading…" />;
  }

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
          gap: '1rem',
          padding: '1.5rem',
          textAlign: 'center',
        }}
      >
        <p role="alert">{error}</p>
        <button type="button" onClick={() => setRetryToken((t) => t + 1)}>
          Retry
        </button>
      </div>
    );
  }

  if (hasAcceptedTerms === true) {
    return <>{children}</>;
  }

  return (
    <TermsAcknowledgmentModal
      onAccept={() => {
        void refetchAfterAccept();
      }}
      onDecline={handleDecline}
    />
  );
}
