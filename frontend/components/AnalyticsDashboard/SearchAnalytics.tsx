import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

interface SearchAnalyticsProps {
  timeRange: number;
}

const SearchAnalytics: React.FC<SearchAnalyticsProps> = ({ timeRange }) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Search Analytics
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Search behavior analytics for the last {timeRange} days will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SearchAnalytics;
