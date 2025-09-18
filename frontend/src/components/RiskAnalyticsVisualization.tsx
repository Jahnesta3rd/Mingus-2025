import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  Divider,
  Switch,
  FormControlLabel
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
  Download,
  FilterList,
  ViewModule,
  ViewList
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
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts';

interface RiskAnalyticsVisualizationProps {
  className?: string;
}

interface HeatMapData {
  industries: string[];
  locations: string[];
  matrix: number[][];
  max_risk: number;
  min_risk: number;
  generated_at: string;
}

interface TrendData {
  date: string;
  total_assessments: number;
  high_risk_users: number;
  successful_outcomes: number;
  successful_transitions: number;
  success_rate: number;
}

interface AccuracyTrend {
  date: string;
  avg_accuracy: number;
  forecast_count: number;
}

const RiskAnalyticsVisualization: React.FC<RiskAnalyticsVisualizationProps> = ({ className }) => {
  const [heatMapData, setHeatMapData] = useState<HeatMapData | null>(null);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [accuracyTrends, setAccuracyTrends] = useState<AccuracyTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState('last_30_days');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showPredictions, setShowPredictions] = useState(true);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch heat map data
      const heatMapResponse = await fetch(`/api/analytics/risk-dashboard/heat-map?analysis_period=30`);
      if (!heatMapResponse.ok) throw new Error('Failed to fetch heat map data');
      const heatMapResult = await heatMapResponse.json();
      setHeatMapData(heatMapResult.heat_map);

      // Fetch trend data
      const trendsResponse = await fetch(`/api/analytics/risk-dashboard/protection-trends?days=30`);
      if (!trendsResponse.ok) throw new Error('Failed to fetch trend data');
      const trendsResult = await trendsResponse.json();
      setTrendData(trendsResult.trends?.trend_data || []);

      // Fetch accuracy trends
      const accuracyResponse = await fetch(`/api/analytics/risk-dashboard/accuracy-trends?days=30`);
      if (!accuracyResponse.ok) throw new Error('Failed to fetch accuracy trends');
      const accuracyResult = await accuracyResponse.json();
      setAccuracyTrends(accuracyResult.trends?.daily_trends || []);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    const interval = setInterval(fetchAnalyticsData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [timePeriod]);

  const getRiskColor = (value: number, maxRisk: number, minRisk: number) => {
    const normalizedValue = (value - minRisk) / (maxRisk - minRisk);
    if (normalizedValue >= 0.8) return '#d32f2f'; // Red
    if (normalizedValue >= 0.6) return '#f57c00'; // Orange
    if (normalizedValue >= 0.4) return '#fbc02d'; // Yellow
    if (normalizedValue >= 0.2) return '#689f38'; // Light Green
    return '#388e3c'; // Green
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;

  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

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
        <IconButton color="inherit" size="small" onClick={fetchAnalyticsData}>
          <Refresh />
        </IconButton>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <Box className={className}>
      {/* Header Controls */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Risk Analytics Visualization
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={timePeriod}
              label="Time Period"
              onChange={(e) => setTimePeriod(e.target.value)}
            >
              <MenuItem value="last_7_days">Last 7 Days</MenuItem>
              <MenuItem value="last_30_days">Last 30 Days</MenuItem>
              <MenuItem value="last_90_days">Last 90 Days</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={showPredictions}
                onChange={(e) => setShowPredictions(e.target.checked)}
              />
            }
            label="Show Predictions"
          />
          
          <IconButton onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
            {viewMode === 'grid' ? <ViewList /> : <ViewModule />}
          </IconButton>
          
          <IconButton onClick={fetchAnalyticsData} disabled={loading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Risk Heat Map */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Heat Map by Industry and Location
              </Typography>
              {heatMapData ? (
                <Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Risk levels across industries and locations
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="caption">Low</Typography>
                      <Box display="flex" gap={0.5}>
                        {[0, 0.25, 0.5, 0.75, 1].map((value) => (
                          <Box
                            key={value}
                            width={20}
                            height={20}
                            bgcolor={getRiskColor(
                              value * (heatMapData.max_risk - heatMapData.min_risk) + heatMapData.min_risk,
                              heatMapData.max_risk,
                              heatMapData.min_risk
                            )}
                            borderRadius={1}
                          />
                        ))}
                      </Box>
                      <Typography variant="caption">High</Typography>
                    </Box>
                  </Box>
                  
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Industry</TableCell>
                          {heatMapData.locations.map((location) => (
                            <TableCell key={location} align="center">
                              {location}
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {heatMapData.industries.map((industry, i) => (
                          <TableRow key={industry}>
                            <TableCell component="th" scope="row">
                              {industry}
                            </TableCell>
                            {heatMapData.locations.map((location, j) => (
                              <TableCell key={location} align="center">
                                <Box
                                  width={40}
                                  height={40}
                                  bgcolor={getRiskColor(
                                    heatMapData.matrix[i][j],
                                    heatMapData.max_risk,
                                    heatMapData.min_risk
                                  )}
                                  borderRadius={1}
                                  display="flex"
                                  alignItems="center"
                                  justifyContent="center"
                                  color="white"
                                  fontWeight="bold"
                                  fontSize="0.75rem"
                                >
                                  {heatMapData.matrix[i][j].toFixed(0)}
                                </Box>
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              ) : (
                <Alert severity="info">No heat map data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Key Metrics Summary */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Key Metrics Summary
              </Typography>
              {trendData.length > 0 ? (
                <Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Total Assessments (30 days)
                    </Typography>
                    <Typography variant="h4">
                      {trendData.reduce((sum, day) => sum + day.total_assessments, 0).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      High Risk Users
                    </Typography>
                    <Typography variant="h4" color="error">
                      {trendData.reduce((sum, day) => sum + day.high_risk_users, 0).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Successful Transitions
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {trendData.reduce((sum, day) => sum + day.successful_transitions, 0).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Average Success Rate
                    </Typography>
                    <Typography variant="h4">
                      {formatPercentage(
                        trendData.reduce((sum, day) => sum + day.success_rate, 0) / trendData.length
                      )}
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">No trend data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Protection Success Trends */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Protection Success Trends
              </Typography>
              {trendData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <RechartsTooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <Legend />
                    <Bar yAxisId="left" dataKey="total_assessments" fill="#8884d8" name="Total Assessments" />
                    <Bar yAxisId="left" dataKey="high_risk_users" fill="#ff7300" name="High Risk Users" />
                    <Bar yAxisId="left" dataKey="successful_transitions" fill="#00c49f" name="Successful Transitions" />
                    <Line 
                      yAxisId="right" 
                      type="monotone" 
                      dataKey="success_rate" 
                      stroke="#8884d8" 
                      strokeWidth={3}
                      name="Success Rate %"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No trend data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Early Warning Accuracy Trends */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Early Warning Accuracy Trends
              </Typography>
              {accuracyTrends.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={accuracyTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis domain={[0, 1]} tickFormatter={(value) => formatPercentage(value * 100)} />
                    <RechartsTooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      formatter={(value) => [formatPercentage(Number(value) * 100), 'Accuracy']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avg_accuracy" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No accuracy trend data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Forecast Count Trends */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Forecast Volume Trends
              </Typography>
              {accuracyTrends.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={accuracyTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis />
                    <RechartsTooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="forecast_count" 
                      stroke="#8884d8" 
                      fill="#8884d8"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No forecast data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Predictive Insights */}
        {showPredictions && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Predictive Insights & Forecasts
                </Typography>
                <Alert severity="info">
                  Advanced predictive analytics and forecasting features will be displayed here.
                  This includes industry risk forecasts, emerging pattern detection, and resource predictions.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default RiskAnalyticsVisualization;
