import { useEffect, useState } from 'react';
import VibeTrackerPage from '../../pages/VibeTrackerPage';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { authJsonHeaders } from './checkupShared';
import { useAuth } from '../../hooks/useAuth';

type PeopleListResponse = {
  people?: unknown[];
};

/**
 * Relationships check-in wrapper (#170).
 * Renders authenticated VibeTrackerPage with dashboard chrome; dark skin overridden via CSS scope.
 */
export function DashRelationshipsCheckup() {
  const { isAuthenticated } = useAuth();
  const [peopleCount, setPeopleCount] = useState<number | null>(null);
  const [lastAssessedAt, setLastAssessedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/vibe-tracker/people', {
          credentials: 'include',
          headers: authJsonHeaders(),
        });
        if (!res.ok) return;
        const data = (await res.json()) as PeopleListResponse & {
          people?: { last_assessed_at?: string | null }[];
        };
        const people = Array.isArray(data.people) ? data.people : [];
        if (cancelled) return;
        setPeopleCount(people.length);
        const dates = people
          .map((p) => p.last_assessed_at)
          .filter((d): d is string => typeof d === 'string' && d.length > 0)
          .sort()
          .reverse();
        setLastAssessedAt(dates[0] ?? null);
      } catch {
        if (!cancelled) setPeopleCount(0);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const headerPill =
    peopleCount == null
      ? undefined
      : peopleCount === 0
        ? 'No one tracked yet'
        : `${peopleCount} ${peopleCount === 1 ? 'person' : 'people'} tracked`;

  return (
    <CheckupWrapperShell
      title="Relationships Check-in"
      headerPill={headerPill}
      lastCompletedAt={lastAssessedAt}
      loading={loading}
    >
      <div className="dash-roster-skin -mx-4 sm:-mx-6 lg:-mx-8">
        <VibeTrackerPage />
      </div>
    </CheckupWrapperShell>
  );
}

export default DashRelationshipsCheckup;
