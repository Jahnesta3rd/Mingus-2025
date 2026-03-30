import { useCallback, useEffect, useState } from 'react';

const SESSION_KEY = 'nps_survey_dismissed';

export interface NpsStatusResponse {
  submitted: boolean;
  days_since_beta_start: number;
  should_show_survey: boolean;
}

export function useNPSSurvey() {
  const [status, setStatus] = useState<NpsStatusResponse | null>(null);
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(SESSION_KEY) === '1';
    } catch {
      return false;
    }
  });

  const reloadStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/feedback/nps/status', { credentials: 'include' });
      if (res.ok) {
        const data = (await res.json()) as NpsStatusResponse;
        setStatus(data);
      }
    } catch {
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    reloadStatus();
  }, [reloadStatus]);

  const markShown = useCallback(() => {
    try {
      sessionStorage.setItem(SESSION_KEY, '1');
    } catch {
      /* ignore */
    }
    setDismissed(true);
  }, []);

  const shouldShow = Boolean(status?.should_show_survey) && !dismissed;

  return { shouldShow, markShown, reloadStatus };
}
