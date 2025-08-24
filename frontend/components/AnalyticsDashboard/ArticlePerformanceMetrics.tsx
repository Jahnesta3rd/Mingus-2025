import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

interface ArticlePerformanceMetricsProps {
  timeRange: number;
}

const ArticlePerformanceMetrics: React.FC<ArticlePerformanceMetricsProps> = ({ timeRange }) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Article Performance Metrics
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Article performance analytics for the last {timeRange} days will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ArticlePerformanceMetrics;
