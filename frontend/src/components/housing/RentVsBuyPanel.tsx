import { useCallback, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';
import { deriveUserTier } from '../fluency';
import {
  HomeownershipActionPlan,
  type GapAnalysisData,
} from './HomeownershipActionPlan';
import {
  RentVsBuyCalculator,
  type GapAnalysisParams,
} from './RentVsBuyCalculator';

type PanelView = 'calculator' | 'plan';

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  return {
    ...csrfHeaders(),
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function RentVsBuyPanel() {
  const { user } = useAuth();
  const userTier = deriveUserTier(user);
  const [view, setView] = useState<PanelView>('calculator');
  const [activeGapAnalysisId, setActiveGapAnalysisId] = useState<number | null>(null);
  const [gapData, setGapData] = useState<GapAnalysisData | null>(null);

  const handlePlanRequested = useCallback(async (params: GapAnalysisParams) => {
    try {
      const res = await fetch('/api/housing/gap-analysis', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify(params),
      });
      if (!res.ok) return;
      const data = (await res.json()) as GapAnalysisData;
      if (data.gap_analysis_id == null) return;
      setActiveGapAnalysisId(data.gap_analysis_id);
      setGapData(data);
      setView('plan');
    } catch {
      /* ignore */
    }
  }, []);

  if (view === 'plan' && activeGapAnalysisId != null && gapData) {
    return (
      <HomeownershipActionPlan
        gapAnalysisId={activeGapAnalysisId}
        userEmail={user?.email ?? ''}
        userTier={userTier}
        gapData={gapData}
        onBack={() => setView('calculator')}
      />
    );
  }

  return (
    <RentVsBuyCalculator
      userEmail={user?.email ?? ''}
      userTier={userTier}
      onPlanRequested={handlePlanRequested}
    />
  );
}

export default RentVsBuyPanel;
