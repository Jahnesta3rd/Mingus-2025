import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

interface TransformationJourneyMetricsProps {
  timeRange: number;
}

const TransformationJourneyMetrics: React.FC<TransformationJourneyMetricsProps> = ({ timeRange }) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Be-Do-Have Transformation Journey Metrics
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Transformation journey analytics for the last {timeRange} days will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TransformationJourneyMetrics;
