import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchWaterfallContext,
  findFluencyCue,
  type FluencyDomain,
  type UserTier,
  type WaterfallContext,
} from '../fluency';
import { CHECKUPS_HUB_PATH } from './checkupShared';

/**
 * Post-submit FluencyCue navigation: auto-navigate after 2s only when no cue matches;
 * defer navigation when a cue is showing until dismiss (500ms) or CTA tap.
 */
export function useCheckupFluencyNavigation(
  domain: FluencyDomain | string,
  userTier: UserTier | string
) {
  const navigate = useNavigate();
  const [waterfallContext, setWaterfallContext] = useState<WaterfallContext | null>(null);
  const autoNavTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearAutoNavTimer = useCallback(() => {
    if (autoNavTimerRef.current != null) {
      clearTimeout(autoNavTimerRef.current);
      autoNavTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => clearAutoNavTimer(), [clearAutoNavTimer]);

  const cueIsShowing = useMemo(() => {
    if (!waterfallContext) return false;
    return findFluencyCue(waterfallContext, domain, userTier) != null;
  }, [waterfallContext, domain, userTier]);

  const scheduleAutoNavigate = useCallback(() => {
    clearAutoNavTimer();
    autoNavTimerRef.current = setTimeout(
      () => navigate(CHECKUPS_HUB_PATH, { replace: true }),
      2000
    );
  }, [clearAutoNavTimer, navigate]);

  const loadFluencyContext = useCallback(async () => {
    try {
      const ctx = await fetchWaterfallContext();
      setWaterfallContext(ctx);
      if (findFluencyCue(ctx, domain, userTier) == null) {
        scheduleAutoNavigate();
      }
    } catch {
      setWaterfallContext(null);
      scheduleAutoNavigate();
    }
  }, [domain, scheduleAutoNavigate, userTier]);

  const onCueActionRoute = useCallback(
    (route: string) => {
      clearAutoNavTimer();
      navigate(route, { replace: true });
    },
    [clearAutoNavTimer, navigate]
  );

  const onCueDismiss = useCallback(() => {
    clearAutoNavTimer();
    autoNavTimerRef.current = setTimeout(
      () => navigate(CHECKUPS_HUB_PATH, { replace: true }),
      500
    );
  }, [clearAutoNavTimer, navigate]);

  return {
    waterfallContext,
    cueIsShowing,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  };
}
