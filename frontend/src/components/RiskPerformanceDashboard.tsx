import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  AlertTitle,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Download as DownloadIcon,
  Assessment as AssessmentIcon,
  Emergency as EmergencyIcon,
  Notifications as NotificationsIcon,
  Memory as MemoryIcon,
  Cpu as CpuIcon,
  Timeline as TimelineIcon,
  HealthAndSafety as HealthIcon
} from '@mui/icons-material';

interface RiskPerformanceMetrics {
  overall_status: string;
  component_status: {
    model_drift: string;
    data_quality: string;
    system_performance: string;
    reliability: string;
    user_engagement: string;
  };
  performance_score: number;
  reliability_score: number;
  data_quality_score: number;
  model_accuracy_score: number;
  user_engagement_score: number;
  critical_alerts: number;
  warning_alerts: number;
  uptime_percentage: number;
}

interface LoadTestResult {
  scenario: string;
  test_duration: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_response_time: number;
  error_rate: number;
  throughput: number;
  peak_cpu_usage: number;
  peak_memory_usage: number;
  concurrent_users: number;
}

interface PerformanceTrend {
  date: string;
  avg_response_time: number;
  response_count: number;
  success_rate: number;
}

const RiskPerformanceDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [healthMetrics, setHealthMetrics] = useState<RiskPerformanceMetrics | null>(null);
  const [loadTestResults, setLoadTestResults] = useState<LoadTestResult[]>([]);
  const [performanceTrends, setPerformanceTrends] = useState<PerformanceTrend[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [selectedTest, setSelectedTest] = useState<string>('');

  // Load data on component mount
  useEffect(() => {
    loadHealthMetrics();
    loadLoadTestResults();
    loadPerformanceTrends();
  }, []);

  const loadHealthMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/risk-performance/health/check');
      const data = await response.json();
      
      if (data.status === 'success') {
        setHealthMetrics(data.health_metrics);
      } else {
        setError('Failed to load health metrics');
      }
    } catch (err) {
      setError('Error loading health metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadLoadTestResults = async () => {
    try {
      const response = await fetch('/api/risk-performance/load-test/analyze');
      const data = await response.json();
      
      if (data.status === 'success') {
        setLoadTestResults(data.analysis.detailed_results || []);
      }
    } catch (err) {
      console.error('Error loading load test results:', err);
    }
  };

  const loadPerformanceTrends = async () => {
    try {
      const response = await fetch('/api/risk-performance/metrics/trends?days=7');
      const data = await response.json();
      
      if (data.status === 'success') {
        setPerformanceTrends(data.trends.emergency_response_trends || []);
      }
    } catch (err) {
      console.error('Error loading performance trends:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'degraded': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return <CheckCircleIcon />;
      case 'warning': return <WarningIcon />;
      case 'degraded': return <ErrorIcon />;
      case 'critical': return <ErrorIcon />;
      default: return <WarningIcon />;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  const formatThroughput = (throughput: number) => {
    return `${throughput.toFixed(1)} req/s`;
  };

  const runLoadTest = async (testType: string) => {
    try {
      setLoading(true);
      let endpoint = '';
      let payload = {};

      switch (testType) {
        case 'high-risk-surge':
          endpoint = '/api/risk-performance/load-test/high-risk-surge';
          payload = { user_count: 200, duration_minutes: 5 };
          break;
        case 'concurrent-unlocks':
          endpoint = '/api/risk-performance/load-test/concurrent-unlocks';
          payload = { concurrent_count: 50 };
          break;
        case 'scalability':
          endpoint = '/api/risk-performance/load-test/scalability';
          payload = { max_concurrent: 100 };
          break;
        case 'notification-capacity':
          endpoint = '/api/risk-performance/load-test/notification-capacity';
          payload = { notification_count: 500 };
          break;
        case 'mixed-load':
          endpoint = '/api/risk-performance/load-test/mixed-load';
          payload = { total_users: 500, duration_minutes: 10 };
          break;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        // Reload test results
        loadLoadTestResults();
        setTestDialogOpen(false);
      } else {
        setError(`Failed to run ${testType} test`);
      }
    } catch (err) {
      setError(`Error running ${testType} test`);
    } finally {
      setLoading(false);
    }
  };

  const startHealthMonitoring = async () => {
    try {
      const response = await fetch('/api/risk-performance/health/start-monitoring', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_minutes: 5 })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setMonitoringActive(true);
      } else {
        setError('Failed to start health monitoring');
      }
    } catch (err) {
      setError('Error starting health monitoring');
    }
  };

  const stopHealthMonitoring = async () => {
    try {
      const response = await fetch('/api/risk-performance/health/stop-monitoring', {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setMonitoringActive(false);
      } else {
        setError('Failed to stop health monitoring');
      }
    } catch (err) {
      setError('Error stopping health monitoring');
    }
  };

  const exportReport = async () => {
    try {
      const response = await fetch('/api/risk-performance/metrics/export?output_path=risk_performance_report.json');
      const data = await response.json();
      
      if (data.status === 'success') {
        // Trigger download
        const link = document.createElement('a');
        link.href = '/risk_performance_report.json';
        link.download = 'risk_performance_report.json';
        link.click();
      } else {
        setError('Failed to export report');
      }
    } catch (err) {
      setError('Error exporting report');
    }
  };

  const TabPanel = ({ children, value, index }: { children: React.ReactNode; value: number; index: number }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Risk Performance Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              loadHealthMetrics();
              loadLoadTestResults();
              loadPerformanceTrends();
            }}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={monitoringActive ? <StopIcon /> : <PlayIcon />}
            onClick={monitoringActive ? stopHealthMonitoring : startHealthMonitoring}
            color={monitoringActive ? 'error' : 'primary'}
          >
            {monitoringActive ? 'Stop Monitoring' : 'Start Monitoring'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={exportReport}
          >
            Export Report
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="System Health" icon={<HealthIcon />} />
        <Tab label="Performance Metrics" icon={<SpeedIcon />} />
        <Tab label="Load Testing" icon={<AssessmentIcon />} />
        <Tab label="Alerts & Monitoring" icon={<NotificationsIcon />} />
      </Tabs>

      {/* System Health Tab */}
      <TabPanel value={activeTab} index={0}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : healthMetrics ? (
          <Grid container spacing={3}>
            {/* Overall Status */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ mr: 2 }}>
                      Overall System Status
                    </Typography>
                    <Chip
                      icon={getStatusIcon(healthMetrics.overall_status)}
                      label={healthMetrics.overall_status.toUpperCase()}
                      color={getStatusColor(healthMetrics.overall_status) as any}
                      size="small"
                    />
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        Uptime
                      </Typography>
                      <Typography variant="h6">
                        {healthMetrics.uptime_percentage.toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        Critical Alerts
                      </Typography>
                      <Typography variant="h6" color="error">
                        {healthMetrics.critical_alerts}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        Warning Alerts
                      </Typography>
                      <Typography variant="h6" color="warning.main">
                        {healthMetrics.warning_alerts}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Component Status */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Component Status
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(healthMetrics.component_status).map(([component, status]) => (
                      <Grid item xs={12} sm={6} md={4} key={component}>
                        <Box sx={{ display: 'flex', alignItems: 'center', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                          <Box sx={{ mr: 2 }}>
                            {getStatusIcon(status)}
                          </Box>
                          <Box>
                            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                              {component.replace('_', ' ')}
                            </Typography>
                            <Chip
                              label={status}
                              color={getStatusColor(status) as any}
                              size="small"
                            />
                          </Box>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Performance Scores */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Performance Scores
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={2.4}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Performance
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthMetrics.performance_score * 100}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="h6">
                          {(healthMetrics.performance_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Reliability
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthMetrics.reliability_score * 100}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="h6">
                          {(healthMetrics.reliability_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Data Quality
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthMetrics.data_quality_score * 100}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="h6">
                          {(healthMetrics.data_quality_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Model Accuracy
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthMetrics.model_accuracy_score * 100}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="h6">
                          {(healthMetrics.model_accuracy_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          User Engagement
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthMetrics.user_engagement_score * 100}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="h6">
                          {(healthMetrics.user_engagement_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Typography>No health metrics available</Typography>
        )}
      </TabPanel>

      {/* Performance Metrics Tab */}
      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          {/* Performance Trends */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Emergency Response Performance Trends
                </Typography>
                {performanceTrends.length > 0 ? (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell align="right">Avg Response Time</TableCell>
                          <TableCell align="right">Response Count</TableCell>
                          <TableCell align="right">Success Rate</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {performanceTrends.map((trend, index) => (
                          <TableRow key={index}>
                            <TableCell>{trend.date}</TableCell>
                            <TableCell align="right">
                              {trend.avg_response_time.toFixed(2)}s
                            </TableCell>
                            <TableCell align="right">{trend.response_count}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${trend.success_rate.toFixed(1)}%`}
                                color={trend.success_rate >= 95 ? 'success' : 'warning'}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography>No performance trends available</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Load Testing Tab */}
      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          {/* Load Test Controls */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Load Testing
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={() => setTestDialogOpen(true)}
                  >
                    Run Test
                  </Button>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Run various load tests to validate system performance under different risk scenarios.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Load Test Results */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Test Results
                </Typography>
                {loadTestResults.length > 0 ? (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Scenario</TableCell>
                          <TableCell align="right">Duration</TableCell>
                          <TableCell align="right">Requests</TableCell>
                          <TableCell align="right">Success Rate</TableCell>
                          <TableCell align="right">Avg Response Time</TableCell>
                          <TableCell align="right">Throughput</TableCell>
                          <TableCell align="right">Peak CPU</TableCell>
                          <TableCell align="right">Peak Memory</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {loadTestResults.map((result, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <Chip
                                label={result.scenario.replace('_', ' ')}
                                color="primary"
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="right">
                              {formatDuration(result.test_duration)}
                            </TableCell>
                            <TableCell align="right">
                              {result.total_requests}
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${((result.successful_requests / result.total_requests) * 100).toFixed(1)}%`}
                                color={result.error_rate <= 5 ? 'success' : 'error'}
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="right">
                              {result.avg_response_time.toFixed(2)}s
                            </TableCell>
                            <TableCell align="right">
                              {formatThroughput(result.throughput)}
                            </TableCell>
                            <TableCell align="right">
                              {result.peak_cpu_usage.toFixed(1)}%
                            </TableCell>
                            <TableCell align="right">
                              {result.peak_memory_usage.toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography>No load test results available</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Alerts & Monitoring Tab */}
      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          {/* Monitoring Status */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Monitoring Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={monitoringActive ? <CheckCircleIcon /> : <ErrorIcon />}
                    label={monitoringActive ? 'Active' : 'Inactive'}
                    color={monitoringActive ? 'success' : 'error'}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Health monitoring is {monitoringActive ? 'running' : 'stopped'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Performance Targets */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Performance Targets
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <SpeedIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Risk Assessment Completion"
                      secondary="Target: <3 seconds"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <EmergencyIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Emergency Unlock Processing"
                      secondary="Target: <2 seconds"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AssessmentIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Risk-triggered Recommendations"
                      secondary="Target: <5 seconds total"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <NotificationsIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Notification Delivery"
                      secondary="Target: <1 second"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <HealthIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="System Availability"
                      secondary="Target: 99.9%"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Load Test Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Load Test</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select a load test scenario to run:
          </Typography>
          <List>
            {[
              { id: 'high-risk-surge', name: 'High-Risk User Surge', description: 'Simulate mass layoff events' },
              { id: 'concurrent-unlocks', name: 'Concurrent Emergency Unlocks', description: 'Test emergency unlock capacity' },
              { id: 'scalability', name: 'Risk Assessment Scalability', description: 'Test with 100+ concurrent assessments' },
              { id: 'notification-capacity', name: 'Notification System Capacity', description: 'Test alert system under load' },
              { id: 'mixed-load', name: 'Mixed Risk Load', description: 'Comprehensive mixed scenario test' }
            ].map((test) => (
              <ListItem
                key={test.id}
                button
                onClick={() => setSelectedTest(test.id)}
                selected={selectedTest === test.id}
              >
                <ListItemText
                  primary={test.name}
                  secondary={test.description}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => runLoadTest(selectedTest)}
            disabled={!selectedTest || loading}
            variant="contained"
          >
            {loading ? 'Running...' : 'Run Test'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RiskPerformanceDashboard;
