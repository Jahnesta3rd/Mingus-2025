import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Badge,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Dashboard,
  Analytics,
  Timeline,
  People,
  AttachMoney,
  Warning,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Refresh,
  Download,
  Settings,
  Insights,
  Assessment,
  Security
} from '@mui/icons-material';

import RiskSuccessDashboard from './RiskSuccessDashboard';
import RiskAnalyticsVisualization from './RiskAnalyticsVisualization';

interface ComprehensiveRiskDashboardProps {
  className?: string;
}

interface DashboardAlert {
  id: string;
  type: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  isActive: boolean;
}

interface OptimizationOpportunity {
  type: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  suggested_actions: string[];
}

const ComprehensiveRiskDashboard: React.FC<ComprehensiveRiskDashboardProps> = ({ className }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [optimizationOpportunities, setOptimizationOpportunities] = useState<OptimizationOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(60000); // 1 minute

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch alerts
      const alertsResponse = await fetch('/api/analytics/risk-dashboard/pattern-changes');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData.pattern_changes || []);
      }

      // Fetch optimization opportunities
      const opportunitiesResponse = await fetch('/api/analytics/risk-dashboard/optimization-opportunities');
      if (opportunitiesResponse.ok) {
        const opportunitiesData = await opportunitiesResponse.json();
        setOptimizationOpportunities(opportunitiesData.opportunities || []);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchDashboardData, refreshInterval);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const handleExportData = () => {
    // Implement data export functionality
    console.log('Exporting dashboard data...');
  };

  const handleSettingsSave = () => {
    setSettingsOpen(false);
    // Implement settings save functionality
  };

  if (loading && activeTab === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box className={className}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Security color="primary" sx={{ fontSize: 32 }} />
          <Box>
            <Typography variant="h4" component="h1">
              Comprehensive Risk Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Career Protection Analytics & Predictive Insights
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" alignItems="center" gap={1}>
          {alerts.length > 0 && (
            <Badge badgeContent={alerts.length} color="error">
              <Warning color="action" />
            </Badge>
          )}
          
          <Tooltip title="Settings">
            <IconButton onClick={() => setSettingsOpen(true)}>
              <Settings />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export Data">
            <IconButton onClick={handleExportData}>
              <Download />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Refresh">
            <IconButton onClick={fetchDashboardData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alerts Banner */}
      {alerts.length > 0 && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => setActiveTab(3)}>
              View All Alerts
            </Button>
          }
        >
          {alerts.length} risk pattern change{alerts.length > 1 ? 's' : ''} detected. 
          Review alerts for immediate action.
        </Alert>
      )}

      {/* Main Tabs */}
      <Card>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            icon={<Dashboard />} 
            label="Overview" 
            iconPosition="start"
          />
          <Tab 
            icon={<Analytics />} 
            label="Analytics" 
            iconPosition="start"
          />
          <Tab 
            icon={<Timeline />} 
            label="Trends" 
            iconPosition="start"
          />
          <Tab 
            icon={<Warning />} 
            label="Alerts" 
            iconPosition="start"
          />
          <Tab 
            icon={<Insights />} 
            label="Insights" 
            iconPosition="start"
          />
          <Tab 
            icon={<People />} 
            label="Success Stories" 
            iconPosition="start"
          />
        </Tabs>

        <CardContent>
          {/* Overview Tab */}
          {activeTab === 0 && (
            <Box>
              <RiskSuccessDashboard />
            </Box>
          )}

          {/* Analytics Tab */}
          {activeTab === 1 && (
            <Box>
              <RiskAnalyticsVisualization />
            </Box>
          )}

          {/* Trends Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Risk Trend Analysis
                </Typography>
                <Alert severity="info">
                  Advanced trend analysis and forecasting features will be displayed here.
                  This includes industry risk trends, market predictions, and user behavior patterns.
                </Alert>
              </Grid>
            </Grid>
          )}

          {/* Alerts Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Risk Alerts & Notifications
              </Typography>
              
              {alerts.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Timestamp</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {alerts.map((alert) => (
                        <TableRow key={alert.id}>
                          <TableCell>
                            <Chip 
                              label={alert.type.replace('_', ' ').toUpperCase()} 
                              size="small" 
                              color="primary"
                            />
                          </TableCell>
                          <TableCell>{alert.title}</TableCell>
                          <TableCell>{alert.description}</TableCell>
                          <TableCell>
                            <Chip 
                              label={alert.severity.toUpperCase()} 
                              size="small" 
                              color={getSeverityColor(alert.severity)}
                            />
                          </TableCell>
                          <TableCell>
                            {new Date(alert.timestamp).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={alert.isActive ? 'Active' : 'Resolved'} 
                              size="small" 
                              color={alert.isActive ? 'error' : 'success'}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="success">
                  No active alerts. All systems operating normally.
                </Alert>
              )}
            </Box>
          )}

          {/* Insights Tab */}
          {activeTab === 4 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Optimization Opportunities
              </Typography>
              
              {optimizationOpportunities.length > 0 ? (
                <Grid container spacing={2}>
                  {optimizationOpportunities.map((opportunity, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                            <Typography variant="h6" component="div">
                              {opportunity.title}
                            </Typography>
                            <Chip 
                              label={opportunity.priority.toUpperCase()} 
                              size="small" 
                              color={getPriorityColor(opportunity.priority)}
                            />
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" paragraph>
                            {opportunity.description}
                          </Typography>
                          
                          <Typography variant="subtitle2" gutterBottom>
                            Suggested Actions:
                          </Typography>
                          <Box component="ul" sx={{ pl: 2, m: 0 }}>
                            {opportunity.suggested_actions.map((action, actionIndex) => (
                              <li key={actionIndex}>
                                <Typography variant="body2">
                                  {action}
                                </Typography>
                              </li>
                            ))}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="info">
                  No optimization opportunities identified at this time.
                </Alert>
              )}
            </Box>
          )}

          {/* Success Stories Tab */}
          {activeTab === 5 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                User Success Stories
              </Typography>
              <Alert severity="info">
                Success stories from risk-based interventions will be displayed here.
                This includes testimonials, case studies, and outcome tracking.
              </Alert>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Dashboard Settings</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              }
              label="Auto Refresh"
            />
            
            <FormControl fullWidth>
              <InputLabel>Refresh Interval</InputLabel>
              <Select
                value={refreshInterval}
                label="Refresh Interval"
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                disabled={!autoRefresh}
              >
                <MenuItem value={30000}>30 seconds</MenuItem>
                <MenuItem value={60000}>1 minute</MenuItem>
                <MenuItem value={300000}>5 minutes</MenuItem>
                <MenuItem value={600000}>10 minutes</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button onClick={handleSettingsSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ComprehensiveRiskDashboard;
