import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  TrendingUp,
  People,
  Article,
  Search,
  Psychology,
  Timeline,
  Refresh,
  Dashboard,
  Analytics,
  Monitor
} from '@mui/icons-material';

import UserEngagementMetrics from './UserEngagementMetrics';
import ArticlePerformanceMetrics from './ArticlePerformanceMetrics';
import SearchAnalytics from './SearchAnalytics';
import CulturalRelevanceMetrics from './CulturalRelevanceMetrics';
import TransformationJourneyMetrics from './TransformationJourneyMetrics';
import SystemPerformanceMetrics from './SystemPerformanceMetrics';
import ContentGapAnalysis from './ContentGapAnalysis';
import ABTestingMetrics from './ABTestingMetrics';

interface DashboardSummary {
  user_metrics: {
    total_users: number;
    active_users: number;
    user_activity_rate_percent: number;
  };
  content_metrics: {
    total_articles: number;
    total_views: number;
    average_views_per_article: number;
  };
  engagement_metrics: {
    total_searches: number;
    search_activity_per_day: number;
  };
  content_gaps: Array<{
    category: string;
    severity: string;
    affected_users: number;
    priority_score: number;
  }>;
  system_health: {
    average_response_time_ms: number;
    success_rate_percent: number;
    cpu_usage_percent: number;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalyticsDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchDashboardSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/analytics/dashboard-summary?days=${timeRange}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard summary');
      }
      
      const data = await response.json();
      setDashboardSummary(data.data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardSummary();
  }, [timeRange]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    fetchDashboardSummary();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  if (loading && !dashboardSummary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Analytics sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Analytics Dashboard
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value as number)}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Dashboard Summary Cards */}
      {dashboardSummary && (
        <Grid container spacing={3} mb={3}>
          {/* User Metrics */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <People sx={{ color: 'primary.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Users
                    </Typography>
                    <Typography variant="h4">
                      {dashboardSummary.user_metrics.total_users.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardSummary.user_metrics.active_users} active ({dashboardSummary.user_metrics.user_activity_rate_percent}%)
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Content Metrics */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <Article sx={{ color: 'success.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Articles
                    </Typography>
                    <Typography variant="h4">
                      {dashboardSummary.content_metrics.total_articles.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardSummary.content_metrics.total_views.toLocaleString()} views
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Engagement Metrics */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <Search sx={{ color: 'info.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Searches
                    </Typography>
                    <Typography variant="h4">
                      {dashboardSummary.engagement_metrics.total_searches.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardSummary.engagement_metrics.search_activity_per_day.toFixed(1)} per day
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* System Health */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <Monitor sx={{ color: 'warning.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      System Health
                    </Typography>
                    <Typography variant="h4">
                      {dashboardSummary.system_health.success_rate_percent.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardSummary.system_health.average_response_time_ms.toFixed(0)}ms avg
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Content Gaps Alert */}
      {dashboardSummary?.content_gaps && dashboardSummary.content_gaps.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'warning.light' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Content Gaps Identified
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {dashboardSummary.content_gaps.map((gap, index) => (
                <Chip
                  key={index}
                  label={`${gap.category} (${gap.affected_users} users)`}
                  color={getSeverityColor(gap.severity) as any}
                  size="small"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Analytics Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics tabs">
            <Tab icon={<People />} label="User Engagement" />
            <Tab icon={<Article />} label="Article Performance" />
            <Tab icon={<Search />} label="Search Analytics" />
            <Tab icon={<Psychology />} label="Cultural Relevance" />
            <Tab icon={<Timeline />} label="Transformation Journey" />
            <Tab icon={<Monitor />} label="System Performance" />
            <Tab icon={<Dashboard />} label="Content Gaps" />
            <Tab icon={<Analytics />} label="A/B Testing" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <UserEngagementMetrics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ArticlePerformanceMetrics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <SearchAnalytics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <CulturalRelevanceMetrics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <TransformationJourneyMetrics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          <SystemPerformanceMetrics timeRange={timeRange} />
        </TabPanel>

        <TabPanel value={tabValue} index={6}>
          <ContentGapAnalysis />
        </TabPanel>

        <TabPanel value={tabValue} index={7}>
          <ABTestingMetrics />
        </TabPanel>
      </Card>

      {/* Last Updated */}
      <Box display="flex" justifyContent="center" mt={2}>
        <Typography variant="body2" color="textSecondary">
          Last updated: {lastUpdated.toLocaleString()}
        </Typography>
      </Box>
    </Box>
  );
};

export default AnalyticsDashboard;
