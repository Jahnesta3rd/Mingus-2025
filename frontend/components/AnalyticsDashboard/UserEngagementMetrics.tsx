import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  LinearProgress
} from '@mui/material';

interface UserEngagementMetricsProps {
  timeRange: number;
}

const UserEngagementMetrics: React.FC<UserEngagementMetricsProps> = ({ timeRange }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchUserEngagement = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/analytics/user-engagement?days=${timeRange}`, {
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch user engagement data');
        }
        
        const result = await response.json();
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchUserEngagement();
  }, [timeRange]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!data) {
    return <Alert severity="info">No user engagement data available</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        User Engagement Analytics
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Analytics
              </Typography>
              <Typography variant="h4">
                {data.session_analytics.total_sessions}
              </Typography>
              <Typography color="textSecondary">
                Total Sessions
              </Typography>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  Average Session Time: {data.session_analytics.average_session_time_minutes.toFixed(1)} minutes
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Engagement
              </Typography>
              <Typography variant="h4">
                {data.content_engagement.total_articles_viewed}
              </Typography>
              <Typography color="textSecondary">
                Articles Viewed
              </Typography>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  Completion Rate: {data.content_engagement.completion_rate_percent.toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UserEngagementMetrics;
