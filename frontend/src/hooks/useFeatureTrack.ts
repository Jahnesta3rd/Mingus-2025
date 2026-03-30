import { useEffect } from 'react';
import { trackEvent } from '../utils/trackEvent';

/**
 * Logs a single "view" when the feature component mounts.
 */
export function useFeatureTrack(
  featureName: string,
  metadata?: Record<string, unknown>
): void {
  useEffect(() => {
    void trackEvent(featureName, 'view', metadata);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: once on mount
  }, []);
}
