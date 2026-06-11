import React from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import VehicleAnalyticsDashboard from './VehicleAnalyticsDashboard';
import BudgetVehicleAnalytics from './BudgetVehicleAnalytics';
import ProfessionalVehicleAnalytics from './ProfessionalVehicleAnalytics';
import { useFeatureTrack } from '../hooks/useFeatureTrack';
import type { AuthUserTier } from '../hooks/useAuth';

interface VehicleAnalyticsRouterProps {
  className?: string;
  userTier: AuthUserTier | null;
  /** Raw tier from user profile (e.g. budget_career_vehicle). */
  rawUserTier?: string;
}

type VehicleSubscriptionTier = 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';

function resolveVehicleSubscriptionTier(
  userTier: AuthUserTier | null,
  rawUserTier?: string
): VehicleSubscriptionTier {
  if (rawUserTier === 'budget_career_vehicle') return 'budget_career_vehicle';
  if (userTier === 'professional') return 'professional';
  if (userTier === 'mid_tier') return 'mid_tier';
  return 'budget';
}

const VehicleAnalyticsRouter: React.FC<VehicleAnalyticsRouterProps> = ({
  className,
  userTier,
  rawUserTier,
}) => {
  useFeatureTrack('vehicle_analytics_dashboard');

  if (userTier === null) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const tier = resolveVehicleSubscriptionTier(userTier, rawUserTier);

  switch (tier) {
    case 'budget':
      return (
        <Box className={className}>
          <BudgetVehicleAnalytics userTier={tier} />
        </Box>
      );

    case 'budget_career_vehicle':
      return (
        <Box className={className}>
          <VehicleAnalyticsDashboard userTier={tier} />
        </Box>
      );

    case 'mid_tier':
      return (
        <Box className={className}>
          <VehicleAnalyticsDashboard userTier={tier} />
        </Box>
      );

    case 'professional':
      return (
        <Box className={className}>
          <ProfessionalVehicleAnalytics />
        </Box>
      );

    default:
      return (
        <Alert severity="error">
          Unknown subscription tier: {tier as string}
        </Alert>
      );
  }
};

export default VehicleAnalyticsRouter;
