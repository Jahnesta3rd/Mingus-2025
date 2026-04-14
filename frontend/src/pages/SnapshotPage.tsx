import React, { useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import MingusSnapshot from '../components/MingusSnapshot';
import { useAuth } from '../hooks/useAuth';

function localDateYmd(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const SnapshotPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  const returnTo = searchParams.get('returnTo') ?? 'dashboard';

  const handleComplete = useCallback(
    (tab: string) => {
      if (tab === 'dashboard') {
        navigate(returnTo === 'dashboard' ? '/dashboard' : `/${returnTo.replace(/^\//, '')}`);
      } else {
        navigate(`/dashboard?tab=${encodeURIComponent(tab)}`);
      }
    },
    [navigate, returnTo],
  );

  useEffect(() => {
    const userId = user?.id;
    if (!userId) return;
    const key = `mingus_snapshot_seen_${userId}_${localDateYmd()}`;
    localStorage.setItem(key, '1');
  }, [user?.id]);

  return <MingusSnapshot onComplete={handleComplete} />;
};

export default SnapshotPage;
