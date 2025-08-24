import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

interface SystemPerformanceMetricsProps {
  timeRange: number;
}

const SystemPerformanceMetrics: React.FC<SystemPerformanceMetricsProps> = ({ timeRange }) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        System Performance Metrics
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            System performance and monitoring data for the last {timeRange} days will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemPerformanceMetrics;
