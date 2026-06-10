import React, { useCallback, useEffect, useState } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

const MINGUS_PURPLE = '#5B2D8E';

interface PlaidStatus {
  connected: boolean;
  connected_at: string | null;
  transaction_count: number;
}

export interface BankConnectorProps {
  onSuccess?: () => void;
}

function buildHeaders(getAccessToken: () => string | null, json = false): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders() };
  if (json) {
    h['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

function formatConnectedDate(iso: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

const BankConnector: React.FC<BankConnectorProps> = ({ onSuccess }) => {
  const { user, getAccessToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [status, setStatus] = useState<PlaidStatus | null>(null);
  const [exchanging, setExchanging] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openRequested, setOpenRequested] = useState(false);

  const tier: 'budget' | 'mid_tier' | 'professional' =
    user?.is_beta === true || user?.tier === 'professional'
      ? 'professional'
      : user?.tier === 'mid_tier'
        ? 'mid_tier'
        : 'budget';

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/plaid/status', {
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) return;
      const data = (await res.json()) as PlaidStatus;
      setStatus(data);
    } catch {
      /* silent */
    }
  }, [getAccessToken]);

  const fetchLinkToken = useCallback(async () => {
    if (tier === 'budget') {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch('/api/plaid/link-token', {
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) {
        setError('Bank connection is temporarily unavailable.');
        return;
      }
      const data = (await res.json()) as { link_token?: string };
      if (data.link_token) {
        setLinkToken(data.link_token);
      }
    } catch {
      setError('Bank connection is temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, tier]);

  useEffect(() => {
    void fetchStatus();
    void fetchLinkToken();
  }, [fetchStatus, fetchLinkToken]);

  const handleExchange = useCallback(
    async (publicToken: string) => {
      setExchanging(true);
      setError(null);
      try {
        const res = await fetch('/api/plaid/exchange-token', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken, true),
          body: JSON.stringify({ public_token: publicToken }),
        });
        if (!res.ok) {
          throw new Error('Could not connect bank');
        }
        await fetchStatus();
        onSuccess?.();
      } catch {
        setError('Could not connect your bank. Please try again.');
      } finally {
        setExchanging(false);
      }
    },
    [fetchStatus, getAccessToken, onSuccess]
  );

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (public_token) => {
      void handleExchange(public_token);
    },
    onExit: () => {
      setOpenRequested(false);
    },
  });

  useEffect(() => {
    if (openRequested && ready) {
      open();
      setOpenRequested(false);
    }
  }, [openRequested, ready, open]);

  const handleDisconnect = async () => {
    setDisconnecting(true);
    setError(null);
    try {
      const res = await fetch('/api/plaid/disconnect', {
        method: 'DELETE',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) {
        throw new Error('Disconnect failed');
      }
      setStatus({ connected: false, connected_at: null, transaction_count: 0 });
      await fetchLinkToken();
    } catch {
      setError('Could not disconnect. Please try again.');
    } finally {
      setDisconnecting(false);
    }
  };

  if (tier === 'budget') {
    return (
      <p
        className="text-[13px] italic"
        style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
      >
        Bank connection is available on Mid-tier and Professional.
      </p>
    );
  }

  if (loading) {
    return (
      <p className="text-sm" style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
        Loading...
      </p>
    );
  }

  if (status?.connected) {
    return (
      <div>
        <p className="text-sm font-medium" style={{ color: 'var(--ink)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
          <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2" aria-hidden />
          Bank connected
        </p>
        {status.connected_at && (
          <p className="mt-1 text-sm" style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
            Connected {formatConnectedDate(status.connected_at)}
          </p>
        )}
        <p className="mt-1 text-sm" style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
          {status.transaction_count} transaction{status.transaction_count === 1 ? '' : 's'} synced
        </p>
        <button
          type="button"
          onClick={() => void handleDisconnect()}
          disabled={disconnecting}
          className="mt-3 underline disabled:opacity-50"
          style={{
            fontFamily: 'Manrope, system-ui, sans-serif',
            fontSize: '13px',
            color: 'var(--ink-mid)',
          }}
        >
          {disconnecting ? 'Disconnecting…' : 'Disconnect'}
        </button>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpenRequested(true)}
        disabled={!linkToken || !ready || exchanging}
        className="rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
        style={{ backgroundColor: MINGUS_PURPLE }}
      >
        {exchanging ? 'Connecting…' : 'Connect your bank'}
      </button>
      <p
        className="mt-2 text-[13px]"
        style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
      >
        Read-only access. We never see your login credentials.
      </p>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default BankConnector;
