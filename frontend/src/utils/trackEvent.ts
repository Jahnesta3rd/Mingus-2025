import { csrfHeaders } from './csrfHeaders';

/**
 * Fire-and-forget client telemetry. Callers should not await (use void trackEvent(...)).
 */
export async function trackEvent(
  featureName: string,
  eventType: 'view' | 'click' | 'export' | 'search' = 'click',
  metadata?: Record<string, unknown>
): Promise<void> {
  try {
    if (typeof window === 'undefined') return;
    const token =
      localStorage.getItem('auth_token') ?? localStorage.getItem('mingus_token');
    if (!token) return;

    const body: Record<string, unknown> = {
      event_type: eventType,
      feature_name: featureName,
    };
    if (metadata !== undefined) {
      body.metadata = metadata;
    }

    const res = await fetch('/api/telemetry/event', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...csrfHeaders(),
      },
      credentials: 'include',
      body: JSON.stringify(body),
    });
    if (res.ok) {
      localStorage.setItem('mingus_last_feature_view', featureName);
    }
  } catch {
    /* silent — telemetry must not affect UX */
  }
}
