import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import FinancialForecastTab from '../components/FinancialForecastTab';
import CardJobHome from '../components/CardJobHome';
import { useAuth } from '../hooks/useAuth';

const FinancialForecastPage: React.FC = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const fromToday = searchParams.get('from') === 'today';
  const cardParam = searchParams.get('card') ?? '2';

  const rawTier = (user as { tier?: string } | null)?.tier;
  const userTier =
    rawTier === 'professional'
      ? 'professional'
      : rawTier === 'mid_tier'
        ? 'mid'
        : 'budget';

  const handleBack = () => {
    navigate('/dashboard/tools?from=today&card=' + cardParam, { replace: true });
  };

  const content = (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <FinancialForecastTab
        userEmail={user?.email ?? ''}
        userTier={userTier}
        className="mt-0"
      />
    </div>
  );

  if (fromToday) {
    return (
      <CardJobHome cardId="cash-snapshot" onBack={handleBack}>
        {content}
      </CardJobHome>
    );
  }

  return content;
};

export default FinancialForecastPage;
