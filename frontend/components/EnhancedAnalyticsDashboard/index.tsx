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
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Divider
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
  Monitor,
  Business,
  Culture,
  RealTime,
  Assessment,
  Bookmark,
  Share
} from '@mui/icons-material';

interface DashboardData {
  period_days: number;
  user_engagement: {
    active_users: number;
    avg_session_time_minutes: number;
    total_article_views: number;
    total_completions: number;
    avg_search_success_rate: number;
    avg_session_duration_minutes: number;
    total_sessions: number;
    avg_articles_per_session: number;
  };
  top_articles: Array<{
    title: string;
    phase: string;
    views: number;
    completion_rate: number;
    cultural_engagement: number;
  }>;
  phase_performance: Array<{
    phase: string;
    article_count: number;
    total_views: number;
    avg_completion_rate: number;
  }>;
  cultural_effectiveness: {
    high_relevance_preference: number;
    community_engagement: number;
    cultural_completion_rate: number;
  };
  search_behavior: {
    total_searches: number;
    click_through_rate: number;
    cultural_search_percentage: number;
  };
}

interface UserJourneyData {
  assessment_distribution: Array<{
    level: string;
    user_count: number;
    avg_be_score: number;
    avg_do_score: number;
    avg_have_score: number;
  }>;
  content_access_patterns: Array<{
    difficulty: string;
    phase: string;
    unique_readers: number;
  }>;
  transformation_journey: Array<{
    current_phase: string;
    user_count: number;
    avg_phase_duration_days: number;
    avg_be_articles: number;
    avg_do_articles: number;
    avg_have_articles: number;
  }>;
}

interface CulturalImpactData {
  content_performance_comparison: Array<{
    content_type: string;
    avg_completion_rate: number;
    avg_bookmark_rate: number;
    avg_rating: number;
    article_count: number;
  }>;
  cultural_engagement_summary: {
    preference_score: number;
    engagement_score: number;
    users_tracked: number;
    avg_cultural_searches: number;
  };
  cultural_search_analysis: {
    cultural_searches: number;
    total_searches: number;
    cultural_search_percentage: number;
    cultural_search_success_rate: number;
  };
}

interface BusinessImpactData {
  conversion_metrics: {
    avg_subscription_conversion_rate: number;
    avg_retention_impact: number;
    articles_analyzed: number;
  };
  retention_analysis: {
    total_users: number;
    returning_users: number;
    retention_rate: number;
  };
  content_roi: {
    avg_cultural_engagement_score: number;
    avg_completion_rate: number;
    avg_bookmark_rate: number;
    avg_share_rate: number;
  };
}

interface RealTimeData {
  last_24_hours: {
    active_users: number;
    article_views: number;
    total_searches: number;
    cultural_searches: number;
    cultural_search_percentage: number;
  };
  timestamp: string;
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
      id={`enhanced-analytics-tabpanel-${index}`}
      aria-labelledby={`enhanced-analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const EnhancedAnalyticsDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [userJourneyData, setUserJourneyData] = useState<UserJourneyData | null>(null);
  const [culturalImpactData, setCulturalImpactData] = useState<CulturalImpactData | null>(null);
  const [businessImpactData, setBusinessImpactData] = useState<BusinessImpactData | null>(null);
  const [realTimeData, setRealTimeData] = useState<RealTimeData | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/analytics/dashboard?days=${timeRange}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      
      const data = await response.json();
      setDashboardData(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserJourneyData = async () => {
    try {
      const response = await fetch('/api/analytics/user-journey', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserJourneyData(data);
      }
    } catch (err) {
      console.error('Error fetching user journey data:', err);
    }
  };

  const fetchCulturalImpactData = async () => {
    try {
      const response = await fetch('/api/analytics/cultural-impact', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCulturalImpactData(data);
      }
    } catch (err) {
      console.error('Error fetching cultural impact data:', err);
    }
  };

  const fetchBusinessImpactData = async () => {
    try {
      const response = await fetch(`/api/analytics/business-impact?days=${timeRange}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setBusinessImpactData(data);
      }
    } catch (err) {
      console.error('Error fetching business impact data:', err);
    }
  };

  const fetchRealTimeData = async () => {
    try {
      const response = await fetch('/api/analytics/real-time-metrics', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRealTimeData(data);
      }
    } catch (err) {
      console.error('Error fetching real-time data:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchUserJourneyData();
    fetchCulturalImpactData();
    fetchBusinessImpactData();
    fetchRealTimeData();
  }, [timeRange]);

  // Auto-refresh real-time data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRealTimeData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    fetchDashboardData();
    fetchUserJourneyData();
    fetchCulturalImpactData();
    fetchBusinessImpactData();
    fetchRealTimeData();
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'BE': return 'primary';
      case 'DO': return 'secondary';
      case 'HAVE': return 'success';
      default: return 'default';
    }
  };

  if (loading && !dashboardData) {
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
            Enhanced Analytics Dashboard
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

      {/* Real-time Metrics Banner */}
      {realTimeData && (
        <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2} mb={1}>
              <RealTime color="primary" />
              <Typography variant="h6">Real-time Metrics (Last 24 Hours)</Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <Typography variant="h4">{realTimeData.last_24_hours.active_users}</Typography>
                <Typography color="textSecondary">Active Users</Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="h4">{realTimeData.last_24_hours.article_views}</Typography>
                <Typography color="textSecondary">Article Views</Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="h4">{realTimeData.last_24_hours.total_searches}</Typography>
                <Typography color="textSecondary">Total Searches</Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="h4">{realTimeData.last_24_hours.cultural_search_percentage}%</Typography>
                <Typography color="textSecondary">Cultural Searches</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Dashboard Summary Cards */}
      {dashboardData && (
        <Grid container spacing={3} mb={3}>
          {/* User Engagement */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <People sx={{ color: 'primary.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Active Users
                    </Typography>
                    <Typography variant="h4">
                      {dashboardData.user_engagement.active_users.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardData.user_engagement.avg_session_time_minutes} min avg session
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Content Performance */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <Article sx={{ color: 'success.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Article Views
                    </Typography>
                    <Typography variant="h4">
                      {dashboardData.user_engagement.total_article_views.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardData.user_engagement.total_completions} completions
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Search Performance */}
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
                      {dashboardData.search_behavior.total_searches.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardData.search_behavior.click_through_rate}% click-through
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Cultural Effectiveness */}
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <Culture sx={{ color: 'warning.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Cultural Preference
                    </Typography>
                    <Typography variant="h4">
                      {dashboardData.cultural_effectiveness.high_relevance_preference}/10
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {dashboardData.cultural_effectiveness.community_engagement}/10 engagement
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Analytics Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="enhanced analytics tabs">
            <Tab icon={<Dashboard />} label="Overview" />
            <Tab icon={<Assessment />} label="User Journey" />
            <Tab icon={<Culture />} label="Cultural Impact" />
            <Tab icon={<Business />} label="Business Impact" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {/* Overview Tab */}
          {dashboardData && (
            <Grid container spacing={3}>
              {/* Top Articles */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Top Performing Articles
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Title</TableCell>
                            <TableCell>Phase</TableCell>
                            <TableCell align="right">Views</TableCell>
                            <TableCell align="right">Completion %</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {dashboardData.top_articles.slice(0, 5).map((article, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                  {article.title}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip 
                                  label={article.phase} 
                                  size="small" 
                                  color={getPhaseColor(article.phase) as any}
                                />
                              </TableCell>
                              <TableCell align="right">{article.views.toLocaleString()}</TableCell>
                              <TableCell align="right">{article.completion_rate}%</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Phase Performance */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Phase Performance
                    </Typography>
                    {dashboardData.phase_performance.map((phase, index) => (
                      <Box key={index} mb={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip 
                              label={phase.phase} 
                              size="small" 
                              color={getPhaseColor(phase.phase) as any}
                            />
                            <Typography variant="body2">
                              {phase.article_count} articles
                            </Typography>
                          </Box>
                          <Typography variant="body2">
                            {phase.avg_completion_rate}% completion
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={phase.avg_completion_rate}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {phase.total_views.toLocaleString()} total views
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* User Journey Tab */}
          {userJourneyData && (
            <Grid container spacing={3}>
              {/* Assessment Distribution */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Assessment Readiness Distribution
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Level</TableCell>
                            <TableCell align="right">Users</TableCell>
                            <TableCell align="right">BE Score</TableCell>
                            <TableCell align="right">DO Score</TableCell>
                            <TableCell align="right">HAVE Score</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {userJourneyData.assessment_distribution.map((assessment, index) => (
                            <TableRow key={index}>
                              <TableCell>{assessment.level}</TableCell>
                              <TableCell align="right">{assessment.user_count}</TableCell>
                              <TableCell align="right">{assessment.avg_be_score}</TableCell>
                              <TableCell align="right">{assessment.avg_do_score}</TableCell>
                              <TableCell align="right">{assessment.avg_have_score}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Transformation Journey */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Transformation Journey Progress
                    </Typography>
                    {userJourneyData.transformation_journey.map((journey, index) => (
                      <Box key={index} mb={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Chip 
                            label={journey.current_phase} 
                            size="small" 
                            color={getPhaseColor(journey.current_phase) as any}
                          />
                          <Typography variant="body2">
                            {journey.user_count} users
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          Avg duration: {journey.avg_phase_duration_days} days
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          BE: {journey.avg_be_articles} | DO: {journey.avg_do_articles} | HAVE: {journey.avg_have_articles} articles
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Cultural Impact Tab */}
          {culturalImpactData && (
            <Grid container spacing={3}>
              {/* Content Performance Comparison */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cultural vs Standard Content Performance
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Content Type</TableCell>
                            <TableCell align="right">Completion %</TableCell>
                            <TableCell align="right">Bookmark %</TableCell>
                            <TableCell align="right">Rating</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {culturalImpactData.content_performance_comparison.map((content, index) => (
                            <TableRow key={index}>
                              <TableCell>{content.content_type}</TableCell>
                              <TableCell align="right">{content.avg_completion_rate}%</TableCell>
                              <TableCell align="right">{content.avg_bookmark_rate}%</TableCell>
                              <TableCell align="right">{content.avg_rating}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Cultural Engagement Summary */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cultural Engagement Summary
                    </Typography>
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        Preference Score
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress 
                          variant="determinate" 
                          value={culturalImpactData.cultural_engagement_summary.preference_score * 10}
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2">
                          {culturalImpactData.cultural_engagement_summary.preference_score}/10
                        </Typography>
                      </Box>
                    </Box>
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        Engagement Score
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress 
                          variant="determinate" 
                          value={culturalImpactData.cultural_engagement_summary.engagement_score * 10}
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2">
                          {culturalImpactData.cultural_engagement_summary.engagement_score}/10
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="textSecondary">
                      {culturalImpactData.cultural_engagement_summary.users_tracked} users tracked
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {culturalImpactData.cultural_engagement_summary.avg_cultural_searches} avg cultural searches
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          {/* Business Impact Tab */}
          {businessImpactData && (
            <Grid container spacing={3}>
              {/* Conversion Metrics */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Conversion Metrics
                    </Typography>
                    <Typography variant="h4" color="primary">
                      {businessImpactData.conversion_metrics.avg_subscription_conversion_rate}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Avg Subscription Conversion Rate
                    </Typography>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6">
                      {businessImpactData.conversion_metrics.avg_retention_impact}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Avg Retention Impact
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Retention Analysis */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      User Retention
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {businessImpactData.retention_analysis.retention_rate}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Retention Rate
                    </Typography>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="body2">
                      {businessImpactData.retention_analysis.returning_users} returning users
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      out of {businessImpactData.retention_analysis.total_users} total
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Content ROI */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Content ROI
                    </Typography>
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        Cultural Engagement
                      </Typography>
                      <Typography variant="h6">
                        {businessImpactData.content_roi.avg_cultural_engagement_score}/10
                      </Typography>
                    </Box>
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        Completion Rate
                      </Typography>
                      <Typography variant="h6">
                        {businessImpactData.content_roi.avg_completion_rate}%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        Bookmark Rate
                      </Typography>
                      <Typography variant="h6">
                        {businessImpactData.content_roi.avg_bookmark_rate}%
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
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

export default EnhancedAnalyticsDashboard;
