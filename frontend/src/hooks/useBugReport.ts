import { useCallback, useRef, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

export function useBugReport() {
  const { getAccessToken } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [phase, setPhase] = useState<'form' | 'submitting' | 'success' | 'error'>('form');
  const [ticketNumber, setTicketNumber] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  const openModal = useCallback(() => {
    setPhase('form');
    setError(null);
    setIsOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (phaseRef.current === 'success') {
      setDescription('');
      setTicketNumber(null);
    }
    setIsOpen(false);
  }, []);

  const submitReport = useCallback(async () => {
    const trimmed = description.trim();
    if (trimmed.length < 10) return;

    setPhase('submitting');
    setError(null);

    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...csrfHeaders(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      const browser_info = navigator.userAgent.slice(0, 200);
      const balance_status = localStorage.getItem('mingus_last_balance_status');
      const last_feature = localStorage.getItem('mingus_last_feature_view');

      const res = await fetch('/api/bug-report/submit', {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({
          description: trimmed,
          current_route: window.location.pathname,
          browser_info,
          balance_status,
          last_feature,
        }),
      });

      if (res.status === 201) {
        const data = (await res.json()) as { ticket_number?: string };
        setTicketNumber(data.ticket_number ?? null);
        setPhase('success');
      } else {
        setPhase('error');
        setError('Something went wrong. Try again.');
      }
    } catch {
      setPhase('error');
      setError('Something went wrong. Try again.');
    }
  }, [description, getAccessToken]);

  return {
    isOpen,
    phase,
    ticketNumber,
    description,
    setDescription,
    error,
    openModal,
    closeModal,
    submitReport,
  };
}
