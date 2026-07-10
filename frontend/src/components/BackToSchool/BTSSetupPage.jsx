import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import BTSDateSetup from './BTSDateSetup';

/**
 * Setup screen wrapper that routes into the purchase plan after BTS1.
 */
export default function BTSSetupPage() {
  const navigate = useNavigate();

  const handleContinue = useCallback(
    (setup) => {
      const sessionId = setup?.sessionId;
      if (!sessionId) return;
      // Plan generation (BTS2) may still be needed; route to plan view which
      // shows a clear 404 if generate-purchase-plan hasn't run yet.
      navigate(`/bts/${sessionId}/plan`);
    },
    [navigate],
  );

  return <BTSDateSetup onContinue={handleContinue} />;
}
