import { useCallback, useState } from 'react';

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

function bearerHeaders(): Record<string, string> {
  const token = localStorage.getItem('mingus_token') || '';
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function jsonAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...bearerHeaders(),
  };
}

export interface VibeTrackedPerson {
  id: string;
  nickname: string;
  emoji: string | null;
  created_at: string | null;
  last_assessed_at: string | null;
  is_archived: boolean;
  archived_at: string | null;
  assessment_count: number;
}

export interface VibePersonTrend {
  id: string;
  tracked_person_id: string;
  trend_direction: string;
  emotional_delta: number | null;
  financial_delta: number | null;
  projection_delta: number | null;
  assessment_count: number;
  last_computed_at: string | null;
  stay_or_go_signal: string | null;
  stay_or_go_confidence: number | null;
}

export interface VibePersonAssessment {
  id: string;
  emotional_score: number;
  financial_score: number;
  verdict_label: string;
  verdict_emoji: string | null;
  annual_projection: number;
  completed_at: string | null;
  lead_id?: string | null;
  notes?: string | null;
}

/** Row from GET /people or /people/archived (list endpoints). */
export interface TrackedPersonListItem extends VibeTrackedPerson {
  trend: VibePersonTrend | null;
  latest_assessment: Omit<VibePersonAssessment, 'lead_id' | 'notes'> | null;
}

/** Full person from GET /people/:id including assessment history. */
export interface TrackedPersonDetail extends VibeTrackedPerson {
  trend: VibePersonTrend | null;
  assessments: VibePersonAssessment[];
}

export interface UseVibeTrackerResult {
  data: TrackedPersonListItem[] | null;
  archivedData: TrackedPersonListItem[] | null;
  loading: boolean;
  error: string | null;
  getPeople: () => Promise<TrackedPersonListItem[]>;
  getArchivedPeople: () => Promise<TrackedPersonListItem[]>;
  getPerson: (personId: string, options?: { trackLoading?: boolean }) => Promise<TrackedPersonDetail>;
  createPerson: (nickname: string, emoji: string | null) => Promise<VibeTrackedPerson>;
  linkAssessment: (personId: string, leadId: string, notes?: string) => Promise<unknown>;
  archivePerson: (personId: string) => Promise<void>;
  unarchivePerson: (personId: string) => Promise<void>;
  deletePerson: (personId: string) => Promise<void>;
}

async function readError(res: Response): Promise<string> {
  let msg = `Request failed (${res.status})`;
  try {
    const j = (await res.json()) as { error?: string; message?: string };
    if (j.error) msg = j.error;
    else if (j.message) msg = j.message;
  } catch {
    /* ignore */
  }
  return msg;
}

function listItemFromPerson(p: VibeTrackedPerson): TrackedPersonListItem {
  return {
    ...p,
    trend: null,
    latest_assessment: null,
  };
}

export function useVibeTracker(): UseVibeTrackerResult {
  const [data, setData] = useState<TrackedPersonListItem[] | null>(null);
  const [archivedData, setArchivedData] = useState<TrackedPersonListItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getPeople = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...bearerHeaders(),
        },
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      const json = (await res.json()) as { people?: TrackedPersonListItem[] };
      const people = json.people ?? [];
      setData(people);
      return people;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not load tracked people';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const getArchivedPeople = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/vibe-tracker/people/archived', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...bearerHeaders(),
        },
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      const json = (await res.json()) as { people?: TrackedPersonListItem[] };
      const people = json.people ?? [];
      setArchivedData(people);
      return people;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not load archived people';
      setError(msg);
      setArchivedData([]);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const getPerson = useCallback(async (personId: string, options?: { trackLoading?: boolean }) => {
    const trackLoading = options?.trackLoading !== false;
    if (trackLoading) {
      setLoading(true);
      setError(null);
    }
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...bearerHeaders(),
        },
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      return (await res.json()) as TrackedPersonDetail;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not load person';
      if (trackLoading) setError(msg);
      throw e;
    } finally {
      if (trackLoading) setLoading(false);
    }
  }, []);

  const createPerson = useCallback(async (nickname: string, emoji: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'POST',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({
          nickname,
          ...(emoji != null && emoji !== '' ? { emoji } : {}),
        }),
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      const person = (await res.json()) as VibeTrackedPerson;
      const row = listItemFromPerson(person);
      setData((prev) => (prev ? [...prev, row] : [row]));
      return person;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not create tracked person';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const linkAssessment = useCallback(async (personId: string, leadId: string, notes?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}/assessment`, {
        method: 'POST',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({
          lead_id: leadId,
          ...(notes != null && notes !== '' ? { notes } : {}),
        }),
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      return res.json();
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not link assessment';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const archivePerson = useCallback(async (personId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}/archive`, {
        method: 'POST',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      const updated = (await res.json()) as TrackedPersonListItem;
      setData((prev) => prev?.filter((p) => p.id !== personId) ?? null);
      setArchivedData((prev) => (prev ? [updated, ...prev] : [updated]));
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not archive';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const unarchivePerson = useCallback(async (personId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}/unarchive`, {
        method: 'POST',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      const updated = (await res.json()) as TrackedPersonListItem;
      setArchivedData((prev) => prev?.filter((p) => p.id !== personId) ?? null);
      setData((prev) => (prev ? [...prev, updated].sort(sortPeopleList) : [updated]));
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not restore';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePerson = useCallback(async (personId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: jsonAuthHeaders(),
        body: JSON.stringify({ confirm: 'DELETE' }),
      });
      if (!res.ok) {
        throw new Error(await readError(res));
      }
      setData((prev) => prev?.filter((p) => p.id !== personId) ?? null);
      setArchivedData((prev) => prev?.filter((p) => p.id !== personId) ?? null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Could not delete';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    data,
    archivedData,
    loading,
    error,
    getPeople,
    getArchivedPeople,
    getPerson,
    createPerson,
    linkAssessment,
    archivePerson,
    unarchivePerson,
    deletePerson,
  };
}

function sortPeopleList(a: TrackedPersonListItem, b: TrackedPersonListItem): number {
  const ta = a.last_assessed_at ? new Date(a.last_assessed_at).getTime() : 0;
  const tb = b.last_assessed_at ? new Date(b.last_assessed_at).getTime() : 0;
  return tb - ta;
}
