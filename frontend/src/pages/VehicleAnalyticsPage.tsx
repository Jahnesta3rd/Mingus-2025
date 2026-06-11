import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import VehicleAnalyticsRouter from '../components/VehicleAnalyticsRouter';
import { useAuth } from '../hooks/useAuth';

const VehicleAnalyticsPage: React.FC = () => {
  const { userTier, user } = useAuth();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Vehicle Analytics
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Comprehensive vehicle cost analysis and optimization insights tailored to your subscription tier.
        </Typography>
      </Box>
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <VehicleAnalyticsRouter userTier={userTier} rawUserTier={user?.tier} />
      </Paper>
    </Container>
  );
};

export default VehicleAnalyticsPage;
