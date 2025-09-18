import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import VehicleAnalyticsDashboard from './VehicleAnalyticsDashboard';
import BudgetVehicleAnalytics from './BudgetVehicleAnalytics';
import ProfessionalVehicleAnalytics from './ProfessionalVehicleAnalytics';

interface VehicleAnalyticsRouterProps {
  className?: string;
}

interface UserTier {
  tier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
  features: {
    showBasicAnalytics: boolean;
    showAdvancedAnalytics: boolean;
    showPeerComparison: boolean;
    showROIAnalysis: boolean;
    showExport: boolean;
    showBusinessFeatures: boolean;
  };
}

const VehicleAnalyticsRouter: React.FC<VehicleAnalyticsRouterProps> = ({
  className
}) => {
  const [loading, setLoading] = useState(true);
  const [userTier, setUserTier] = useState<UserTier | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserTier = async () => {
      try {
        setLoading(true);
        
        // In a real implementation, this would fetch from the API
        // For now, we'll use a mock implementation
        const mockUserTier = await new Promise<UserTier>((resolve) => {
          setTimeout(() => {
            // Mock user tier - in real app, this would come from user context or API
            const tier = 'mid_tier'; // This would be dynamic
            
            const tierConfig = {
              budget: {
                tier: 'budget' as const,
                features: {
                  showBasicAnalytics: true,
                  showAdvancedAnalytics: false,
                  showPeerComparison: false,
                  showROIAnalysis: false,
                  showExport: false,
                  showBusinessFeatures: false
                }
              },
              budget_career_vehicle: {
                tier: 'budget_career_vehicle' as const,
                features: {
                  showBasicAnalytics: true,
                  showAdvancedAnalytics: false,
                  showPeerComparison: true,
                  showROIAnalysis: false,
                  showExport: false,
                  showBusinessFeatures: false
                }
              },
              mid_tier: {
                tier: 'mid_tier' as const,
                features: {
                  showBasicAnalytics: true,
                  showAdvancedAnalytics: true,
                  showPeerComparison: true,
                  showROIAnalysis: true,
                  showExport: false,
                  showBusinessFeatures: false
                }
              },
              professional: {
                tier: 'professional' as const,
                features: {
                  showBasicAnalytics: true,
                  showAdvancedAnalytics: true,
                  showPeerComparison: true,
                  showROIAnalysis: true,
                  showExport: true,
                  showBusinessFeatures: true
                }
              }
            };
            
            resolve(tierConfig[tier]);
          }, 1000);
        });
        
        setUserTier(mockUserTier);
        setLoading(false);
      } catch (err) {
        setError('Failed to load user tier information');
        setLoading(false);
      }
    };

    fetchUserTier();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  if (!userTier) {
    return (
      <Alert severity="error">
        Unable to determine user subscription tier
      </Alert>
    );
  }

  // Route to appropriate component based on user tier
  switch (userTier.tier) {
    case 'budget':
      return (
        <Box className={className}>
          <BudgetVehicleAnalytics userTier={userTier.tier} />
        </Box>
      );
    
    case 'budget_career_vehicle':
      return (
        <Box className={className}>
          <VehicleAnalyticsDashboard userTier={userTier.tier} />
        </Box>
      );
    
    case 'mid_tier':
      return (
        <Box className={className}>
          <VehicleAnalyticsDashboard userTier={userTier.tier} />
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
          Unknown subscription tier: {userTier.tier}
        </Alert>
      );
  }
};

export default VehicleAnalyticsRouter;
