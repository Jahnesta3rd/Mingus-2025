import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Badge,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  People,
  AttachMoney,
  Timeline,
  Assessment,
  Insights,
  Refresh,
  Download
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Heatmap
} from 'recharts';

interface RiskSuccessDashboardProps {
  className?: string;
}

interface DashboardMetrics {
  career_protection_metrics: {
    career_protection_success_rate: number;
    early_warning_accuracy: number;
    risk_intervention_effectiveness: number;
    income_protection_rate: number;
    unemployment_prevention_rate: number;
  };
  user_journey_analytics: {
    risk_to_outcome_funnel: any;
    proactive_vs_reactive_comparison: any;
    risk_communication_effectiveness: any;
    emergency_unlock_conversion: any;
  };
  predictive_insights: any;
  risk_trend_analysis: any;
}

interface SuccessStory {
  user_id: string;
  story_type: string;
  story_title: string;
  story_description: string;
  user_satisfaction: number;
  would_recommend: boolean;
  created_date: string;
}

const RiskSuccessDashboard: React.FC<RiskSuccessDashboardProps> = ({ className }) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [successStories, setSuccessStories] = useState<SuccessStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch protection metrics
      const metricsResponse = await fetch('/api/analytics/risk-dashboard/protection-metrics?time_period=last_30_days');
      if (!metricsResponse.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData.metrics);

      // Fetch success stories
      const storiesResponse = await fetch('/api/analytics/risk-dashboard/success-stories?limit=5');
      if (!storiesResponse.ok) throw new Error('Failed to fetch success stories');
      const storiesData = await storiesResponse.json();
      setSuccessStories(storiesData.stories);

      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getMetricColor = (value: number, threshold: number = 70) => {
    if (value >= threshold) return 'success';
    if (value >= threshold * 0.8) return 'warning';
    return 'error';
  };

  const getMetricIcon = (value: number, threshold: number = 70) => {
    if (value >= threshold) return <CheckCircle color="success" />;
    if (value >= threshold * 0.8) return <Warning color="warning" />;
    return <Warning color="error" />;
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <IconButton color="inherit" size="small" onClick={fetchDashboardData}>
          <Refresh />
        </IconButton>
      }>
        {error}
      </Alert>
    );
  }

  if (!metrics) {
    return (
      <Alert severity="info">
        No data available. Please check your connection and try again.
      </Alert>
    );
  }

  const protectionMetrics = metrics.career_protection_metrics;
  const userJourney = metrics.user_journey_analytics;

  // Prepare chart data
  const funnelData = userJourney.risk_to_outcome_funnel?.funnel_steps ? [
    { name: 'Risk Detected', value: userJourney.risk_to_outcome_funnel.funnel_steps.users_at_risk },
    { name: 'Intervention Triggered', value: userJourney.risk_to_outcome_funnel.funnel_steps.users_with_interventions },
    { name: 'Successful Transition', value: userJourney.risk_to_outcome_funnel.funnel_steps.users_with_successful_transitions },
    { name: 'Salary Increased', value: userJourney.risk_to_outcome_funnel.funnel_steps.users_with_salary_increases }
  ] : [];

  const outcomeDistribution = [
    { name: 'Successful Transitions', value: 45, color: '#00C49F' },
    { name: 'Salary Increases', value: 35, color: '#0088FE' },
    { name: 'Unemployment Prevented', value: 20, color: '#FFBB28' }
  ];

  return (
    <Box className={className}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Risk Success Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          {lastUpdated && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <IconButton onClick={fetchDashboardData} disabled={loading}>
            <Refresh />
          </IconButton>
          <IconButton>
            <Download />
          </IconButton>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Protection Success Rate
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatPercentage(protectionMetrics.career_protection_success_rate)}
                  </Typography>
                </Box>
                {getMetricIcon(protectionMetrics.career_protection_success_rate)}
              </Box>
              <LinearProgress
                variant="determinate"
                value={protectionMetrics.career_protection_success_rate}
                color={getMetricColor(protectionMetrics.career_protection_success_rate)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Early Warning Accuracy
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatPercentage(protectionMetrics.early_warning_accuracy)}
                  </Typography>
                </Box>
                {getMetricIcon(protectionMetrics.early_warning_accuracy)}
              </Box>
              <LinearProgress
                variant="determinate"
                value={protectionMetrics.early_warning_accuracy}
                color={getMetricColor(protectionMetrics.early_warning_accuracy)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Intervention Effectiveness
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatPercentage(protectionMetrics.risk_intervention_effectiveness)}
                  </Typography>
                </Box>
                {getMetricIcon(protectionMetrics.risk_intervention_effectiveness)}
              </Box>
              <LinearProgress
                variant="determinate"
                value={protectionMetrics.risk_intervention_effectiveness}
                color={getMetricColor(protectionMetrics.risk_intervention_effectiveness)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Income Protection Rate
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatPercentage(protectionMetrics.income_protection_rate)}
                  </Typography>
                </Box>
                {getMetricIcon(protectionMetrics.income_protection_rate)}
              </Box>
              <LinearProgress
                variant="determinate"
                value={protectionMetrics.income_protection_rate}
                color={getMetricColor(protectionMetrics.income_protection_rate)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Unemployment Prevention
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatPercentage(protectionMetrics.unemployment_prevention_rate)}
                  </Typography>
                </Box>
                {getMetricIcon(protectionMetrics.unemployment_prevention_rate)}
              </Box>
              <LinearProgress
                variant="determinate"
                value={protectionMetrics.unemployment_prevention_rate}
                color={getMetricColor(protectionMetrics.unemployment_prevention_rate)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different views */}
      <Card>
        <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
          <Tab label="Overview" />
          <Tab label="User Journey" />
          <Tab label="Predictive Analytics" />
          <Tab label="Success Stories" />
          <Tab label="ROI Analysis" />
        </Tabs>

        <CardContent>
          {/* Overview Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Risk to Outcome Funnel
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={funnelData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Outcome Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={outcomeDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {outcomeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Grid>
            </Grid>
          )}

          {/* User Journey Tab */}
          {activeTab === 1 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Proactive vs Reactive Comparison
                </Typography>
                {userJourney.proactive_vs_reactive_comparison && (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell align="right">Proactive Users</TableCell>
                          <TableCell align="right">Reactive Users</TableCell>
                          <TableCell align="right">Difference</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Count</TableCell>
                          <TableCell align="right">
                            {userJourney.proactive_vs_reactive_comparison.proactive_users?.count || 0}
                          </TableCell>
                          <TableCell align="right">
                            {userJourney.proactive_vs_reactive_comparison.reactive_users?.count || 0}
                          </TableCell>
                          <TableCell align="right">
                            {(userJourney.proactive_vs_reactive_comparison.proactive_users?.count || 0) - 
                             (userJourney.proactive_vs_reactive_comparison.reactive_users?.count || 0)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Avg Salary Change</TableCell>
                          <TableCell align="right">
                            ${userJourney.proactive_vs_reactive_comparison.proactive_users?.avg_salary_change || 0}
                          </TableCell>
                          <TableCell align="right">
                            ${userJourney.proactive_vs_reactive_comparison.reactive_users?.avg_salary_change || 0}
                          </TableCell>
                          <TableCell align="right">
                            ${userJourney.proactive_vs_reactive_comparison.comparison?.salary_change_difference || 0}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Avg Time to Role (days)</TableCell>
                          <TableCell align="right">
                            {userJourney.proactive_vs_reactive_comparison.proactive_users?.avg_time_to_role_days || 0}
                          </TableCell>
                          <TableCell align="right">
                            {userJourney.proactive_vs_reactive_comparison.reactive_users?.avg_time_to_role_days || 0}
                          </TableCell>
                          <TableCell align="right">
                            {userJourney.proactive_vs_reactive_comparison.comparison?.time_difference_days || 0}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Grid>
            </Grid>
          )}

          {/* Predictive Analytics Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Risk Forecasts
                </Typography>
                <Alert severity="info">
                  Predictive analytics data will be displayed here once forecasts are generated.
                </Alert>
              </Grid>
            </Grid>
          )}

          {/* Success Stories Tab */}
          {activeTab === 3 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Recent Success Stories
                </Typography>
                {successStories.length > 0 ? (
                  <Grid container spacing={2}>
                    {successStories.map((story, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                              <Typography variant="h6" component="div">
                                {story.story_title}
                              </Typography>
                              <Chip
                                label={story.story_type.replace('_', ' ').toUpperCase()}
                                size="small"
                                color="primary"
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary" paragraph>
                              {story.story_description}
                            </Typography>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Box display="flex" alignItems="center" gap={1}>
                                <Typography variant="body2" color="text.secondary">
                                  Satisfaction: {story.user_satisfaction}/5
                                </Typography>
                                {story.would_recommend && (
                                  <Chip label="Would Recommend" size="small" color="success" />
                                )}
                              </Box>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(story.created_date).toLocaleDateString()}
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Alert severity="info">
                    No success stories available at the moment.
                  </Alert>
                )}
              </Grid>
            </Grid>
          )}

          {/* ROI Analysis Tab */}
          {activeTab === 4 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Return on Investment Analysis
                </Typography>
                <Alert severity="info">
                  ROI analysis data will be displayed here once calculated.
                </Alert>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default RiskSuccessDashboard;
