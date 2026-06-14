import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { deriveUserTier } from '../fluency';
import { HomeownershipActionPlan } from './HomeownershipActionPlan';
import { RentVsBuyCalculator } from './RentVsBuyCalculator';

type PanelView = 'calculator' | 'plan';

export function RentVsBuyPanel() {
  const { user } = useAuth();
  const userTier = deriveUserTier(user);
  const [view, setView] = useState<PanelView>('calculator');
  const [activeGapAnalysisId, setActiveGapAnalysisId] = useState<number | null>(null);

  if (view === 'plan' && activeGapAnalysisId != null) {
    return (
      <HomeownershipActionPlan
        gapAnalysisId={activeGapAnalysisId}
        userTier={userTier}
        onBack={() => setView('calculator')}
      />
    );
  }

  return (
    <RentVsBuyCalculator
      userEmail={user?.email ?? ''}
      userTier={userTier}
      onPlanRequested={(gapId) => {
        setActiveGapAnalysisId(gapId);
        setView('plan');
      }}
    />
  );
}

export default RentVsBuyPanel;
