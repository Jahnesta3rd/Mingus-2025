import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import MingusSnapshot from '../components/MingusSnapshot';
import AddImportantDateModal from '../components/important-dates/AddImportantDateModal';
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
  const [addImportantDateOpen, setAddImportantDateOpen] = useState(false);
  const [snapshotReloadKey, setSnapshotReloadKey] = useState(0);

  const returnTo = searchParams.get('returnTo') ?? 'dashboard';

  const handleComplete = useCallback(
    (tab: string) => {
      if (tab === 'dashboard') {
        navigate(returnTo === 'dashboard' ? '/dashboard' : `/${returnTo.replace(/^\//, '')}`);
      } else if (tab === 'milestones' || tab === 'important-dates') {
        navigate('/dashboard/tools?tab=overview&editProfile=1');
      } else {
        navigate(`/dashboard?tab=${encodeURIComponent(tab)}`);
      }
    },
    [navigate, returnTo],
  );

  const handleImportantDateSaved = useCallback(() => {
    setAddImportantDateOpen(false);
    setSnapshotReloadKey((k) => k + 1);
  }, []);

  useEffect(() => {
    const userId = user?.id;
    if (!userId) return;
    const key = `mingus_snapshot_seen_${userId}_${localDateYmd()}`;
    localStorage.setItem(key, '1');
  }, [user?.id]);

  const userId = user?.id ?? '';

  return (
    <>
      <MingusSnapshot
        onComplete={handleComplete}
        onOpenAddImportantDate={() => setAddImportantDateOpen(true)}
        snapshotReloadKey={snapshotReloadKey}
      />
      {userId ? (
        <AddImportantDateModal
          isOpen={addImportantDateOpen}
          onClose={() => setAddImportantDateOpen(false)}
          userId={userId}
          onSaved={handleImportantDateSaved}
        />
      ) : null}
    </>
  );
};

export default SnapshotPage;
