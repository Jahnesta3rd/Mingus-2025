import { useState, useEffect } from 'react';

export function useSeanEllisSurvey() {
  const [shouldShow, setShouldShow] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    // Don't show if already dismissed this session
    if (sessionStorage.getItem('sean_ellis_dismissed')) return;

    fetch('/api/feedback/sean-ellis/status', {
      credentials: 'include',
      headers: { Authorization: `Bearer ${localStorage.getItem('mingus_token')}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.should_show) setShouldShow(true);
        if (data.submitted) setSubmitted(true);
      })
      .catch(() => {}); // silent — never break the dashboard
  }, []);

  const dismiss = () => {
    sessionStorage.setItem('sean_ellis_dismissed', '1');
    setShouldShow(false);
  };

  const markSubmitted = () => {
    setSubmitted(true);
    setShouldShow(false);
    sessionStorage.setItem('sean_ellis_dismissed', '1');
  };

  return { shouldShow, submitted, dismiss, markSubmitted };
}
