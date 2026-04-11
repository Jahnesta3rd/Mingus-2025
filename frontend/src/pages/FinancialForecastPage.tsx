import React from 'react';
import FinancialForecastTab from '../components/FinancialForecastTab';
import { useAuth } from '../hooks/useAuth';

const FinancialForecastPage: React.FC = () => {
  const { user } = useAuth();
  const rawTier = (user as { tier?: string } | null)?.tier;
  const userTier =
    rawTier === 'professional'
      ? 'professional'
      : rawTier === 'mid_tier'
        ? 'mid'
        : 'budget';

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <FinancialForecastTab
        userEmail={user?.email ?? ''}
        userTier={userTier}
        className="mt-0"
      />
    </div>
  );
};

export default FinancialForecastPage;
