export const VIBE_CHECKUPS_UTM_STORAGE_KEY = "vibe_checkups_utm";

export type VibeCheckupsUtm = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

export function captureVibeCheckupsUtmFromSearch(search: string): VibeCheckupsUtm {
  const params = new URLSearchParams(search);
  const utm: VibeCheckupsUtm = {};
  const source = params.get("utm_source");
  const medium = params.get("utm_medium");
  const campaign = params.get("utm_campaign");
  if (source) utm.utm_source = source;
  if (medium) utm.utm_medium = medium;
  if (campaign) utm.utm_campaign = campaign;
  return utm;
}

/** Merges new params into sessionStorage so refreshes with different UTMs update attribution. */
export function persistVibeCheckupsUtm(utm: VibeCheckupsUtm): void {
  if (!utm.utm_source && !utm.utm_medium && !utm.utm_campaign) return;
  const prev = getStoredVibeCheckupsUtm();
  const merged: VibeCheckupsUtm = { ...prev, ...utm };
  sessionStorage.setItem(VIBE_CHECKUPS_UTM_STORAGE_KEY, JSON.stringify(merged));
}

export function getStoredVibeCheckupsUtm(): VibeCheckupsUtm | null {
  try {
    const raw = sessionStorage.getItem(VIBE_CHECKUPS_UTM_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as VibeCheckupsUtm;
  } catch {
    return null;
  }
}
