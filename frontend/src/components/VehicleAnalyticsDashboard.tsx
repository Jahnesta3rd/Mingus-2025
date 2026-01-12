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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  Dashboard,
  Analytics,
  Timeline,
  AttachMoney,
  LocalGasStation,
  Build,
  TrendingUp,
  TrendingDown,
  Refresh,
  Download,
  GitCompare,
  Assessment,
  Insights,
  Warning,
  CheckCircle,
  Speed,
  DirectionsCar
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

interface VehicleAnalyticsDashboardProps {
  className?: string;
  userTier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
}

interface VehicleAnalyticsData {
  costTrends: Array<{
    date: string;
    totalCost: number;
    fuelCost: number;
    maintenanceCost: number;
    insuranceCost: number;
    otherCost: number;
  }>;
  maintenanceAccuracy: {
    predicted: number;
    actual: number;
    accuracy: number;
    savings: number;
  };
  fuelEfficiency: Array<{
    month: string;
    mpg: number;
    costPerMile: number;
    totalMiles: number;
    fuelCost: number;
  }>;
  costPerMile: {
    current: number;
    average: number;
    trend: 'up' | 'down' | 'stable';
    breakdown: {
      fuel: number;
      maintenance: number;
      depreciation: number;
      insurance: number;
    };
  };
  peerComparison: {
    yourCostPerMile: number;
    peerAverage: number;
    percentile: number;
    savings: number;
  };
  roiAnalysis: {
    vehicleInvestment: number;
    totalSavings: number;
    roi: number;
    paybackPeriod: number;
    recommendations: string[];
  };
  exportData?: any;
}

const VehicleAnalyticsDashboard: React.FC<VehicleAnalyticsDashboardProps> = ({
  className,
  userTier
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<VehicleAnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState('6months');
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');

  // Mock data - in real implementation, this would come from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setData({
        costTrends: [
          { date: '2024-01', totalCost: 450, fuelCost: 200, maintenanceCost: 150, insuranceCost: 80, otherCost: 20 },
          { date: '2024-02', totalCost: 520, fuelCost: 220, maintenanceCost: 200, insuranceCost: 80, otherCost: 20 },
          { date: '2024-03', totalCost: 480, fuelCost: 180, maintenanceCost: 220, insuranceCost: 80, otherCost: 0 },
          { date: '2024-04', totalCost: 600, fuelCost: 250, maintenanceCost: 250, insuranceCost: 80, otherCost: 20 },
          { date: '2024-05', totalCost: 420, fuelCost: 200, maintenanceCost: 120, insuranceCost: 80, otherCost: 20 },
          { date: '2024-06', totalCost: 550, fuelCost: 230, maintenanceCost: 200, insuranceCost: 80, otherCost: 40 }
        ],
        maintenanceAccuracy: {
          predicted: 1200,
          actual: 1150,
          accuracy: 95.8,
          savings: 50
        },
        fuelEfficiency: [
          { month: 'Jan', mpg: 28.5, costPerMile: 0.12, totalMiles: 1200, fuelCost: 144 },
          { month: 'Feb', mpg: 29.2, costPerMile: 0.11, totalMiles: 1100, fuelCost: 121 },
          { month: 'Mar', mpg: 27.8, costPerMile: 0.13, totalMiles: 1300, fuelCost: 169 },
          { month: 'Apr', mpg: 30.1, costPerMile: 0.10, totalMiles: 1000, fuelCost: 100 },
          { month: 'May', mpg: 28.9, costPerMile: 0.12, totalMiles: 1250, fuelCost: 150 },
          { month: 'Jun', mpg: 29.5, costPerMile: 0.11, totalMiles: 1150, fuelCost: 127 }
        ],
        costPerMile: {
          current: 0.45,
          average: 0.48,
          trend: 'down',
          breakdown: {
            fuel: 0.12,
            maintenance: 0.15,
            depreciation: 0.12,
            insurance: 0.06
          }
        },
        peerComparison: {
          yourCostPerMile: 0.45,
          peerAverage: 0.52,
          percentile: 25,
          savings: 0.07
        },
        roiAnalysis: {
          vehicleInvestment: 25000,
          totalSavings: 3500,
          roi: 14.0,
          paybackPeriod: 7.1,
          recommendations: [
            'Consider fuel-efficient driving techniques',
            'Regular maintenance can reduce long-term costs',
            'Compare insurance rates annually'
          ]
        }
      });
      setLoading(false);
    };

    fetchData();
  }, [timeRange]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleExport = () => {
    if (userTier !== 'professional') {
      alert('Export functionality is only available for Professional tier users');
      return;
    }
    setExportDialogOpen(true);
  };

  const getTierFeatures = () => {
    switch (userTier) {
      case 'budget':
        return {
          showBasicAnalytics: true,
          showAdvancedAnalytics: false,
          showPeerComparison: false,
          showROIAnalysis: false,
          showExport: false
        };
      case 'budget_career_vehicle':
        return {
          showBasicAnalytics: true,
          showAdvancedAnalytics: false,
          showPeerComparison: true,
          showROIAnalysis: false,
          showExport: false
        };
      case 'mid_tier':
        return {
          showBasicAnalytics: true,
          showAdvancedAnalytics: true,
          showPeerComparison: true,
          showROIAnalysis: true,
          showExport: false
        };
      case 'professional':
        return {
          showBasicAnalytics: true,
          showAdvancedAnalytics: true,
          showPeerComparison: true,
          showROIAnalysis: true,
          showExport: true
        };
      default:
        return {
          showBasicAnalytics: false,
          showAdvancedAnalytics: false,
          showPeerComparison: false,
          showROIAnalysis: false,
          showExport: false
        };
    }
  };

  const features = getTierFeatures();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Failed to load vehicle analytics data. Please try again.
      </Alert>
    );
  }

  const tabs = [
    { label: 'Cost Trends', icon: <Timeline />, available: features.showBasicAnalytics },
    { label: 'Maintenance', icon: <Build />, available: features.showBasicAnalytics },
    { label: 'Fuel Efficiency', icon: <LocalGasStation />, available: features.showBasicAnalytics },
    { label: 'Cost Analysis', icon: <AttachMoney />, available: features.showAdvancedAnalytics },
    { label: 'Peer Comparison', icon: <GitCompare />, available: features.showPeerComparison },
    { label: 'ROI Analysis', icon: <Assessment />, available: features.showROIAnalysis }
  ].filter(tab => tab.available);

  return (
    <Box className={className}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Vehicle Analytics Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Comprehensive vehicle cost analysis and optimization insights
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="3months">3 Months</MenuItem>
              <MenuItem value="6months">6 Months</MenuItem>
              <MenuItem value="1year">1 Year</MenuItem>
              <MenuItem value="2years">2 Years</MenuItem>
            </Select>
          </FormControl>
          {features.showExport && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExport}
            >
              Export Data
            </Button>
          )}
          <IconButton onClick={() => window.location.reload()}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Tier-specific feature notice */}
      {userTier === 'budget' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          You're viewing basic analytics. Upgrade to Mid-tier or Professional for advanced features like peer comparison and ROI analysis.
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={tab.label}
              icon={tab.icon}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Box>

      {/* Tab Content */}
      <Box>
        {activeTab === 0 && features.showBasicAnalytics && (
          <CostTrendsTab data={data.costTrends} />
        )}
        {activeTab === 1 && features.showBasicAnalytics && (
          <MaintenanceTab data={data.maintenanceAccuracy} />
        )}
        {activeTab === 2 && features.showBasicAnalytics && (
          <FuelEfficiencyTab data={data.fuelEfficiency} />
        )}
        {activeTab === 3 && features.showAdvancedAnalytics && (
          <CostAnalysisTab data={data.costPerMile} />
        )}
        {activeTab === 4 && features.showPeerComparison && (
          <PeerComparisonTab data={data.peerComparison} />
        )}
        {activeTab === 5 && features.showROIAnalysis && (
          <ROIAnalysisTab data={data.roiAnalysis} />
        )}
      </Box>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Vehicle Analytics Data</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Export Format</InputLabel>
            <Select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              label="Export Format"
            >
              <MenuItem value="csv">CSV</MenuItem>
              <MenuItem value="excel">Excel</MenuItem>
              <MenuItem value="pdf">PDF Report</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => {
            // Handle export logic here
            setExportDialogOpen(false);
            alert(`Exporting data as ${exportFormat.toUpperCase()}`);
          }} variant="contained">
            Export
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Individual Tab Components
const CostTrendsTab: React.FC<{ data: VehicleAnalyticsData['costTrends'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Vehicle Cost Trends Over Time
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Area type="monotone" dataKey="totalCost" stackId="1" stroke="#8884d8" fill="#8884d8" />
              <Bar dataKey="fuelCost" stackId="2" fill="#82ca9d" />
              <Bar dataKey="maintenanceCost" stackId="2" fill="#ffc658" />
              <Bar dataKey="insuranceCost" stackId="2" fill="#ff7300" />
              <Bar dataKey="otherCost" stackId="2" fill="#8dd1e1" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const MaintenanceTab: React.FC<{ data: VehicleAnalyticsData['maintenanceAccuracy'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Maintenance Prediction Accuracy
          </Typography>
          <Box display="flex" alignItems="center" mb={2}>
            <Typography variant="h3" color="primary">
              {data.accuracy}%
            </Typography>
            <Box ml={2}>
              <Typography variant="body2" color="text.secondary">
                Prediction Accuracy
              </Typography>
              <Typography variant="body2" color="success.main">
                +${data.savings} saved
              </Typography>
            </Box>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={data.accuracy} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Breakdown
          </Typography>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Predicted Cost:</Typography>
            <Typography>${data.predicted}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Actual Cost:</Typography>
            <Typography>${data.actual}</Typography>
          </Box>
          <Divider sx={{ my: 1 }} />
          <Box display="flex" justifyContent="space-between">
            <Typography variant="subtitle2">Savings:</Typography>
            <Typography variant="subtitle2" color="success.main">
              +${data.savings}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const FuelEfficiencyTab: React.FC<{ data: VehicleAnalyticsData['fuelEfficiency'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={8}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Fuel Efficiency Trends
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="mpg" stroke="#8884d8" strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="costPerMile" stroke="#82ca9d" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={4}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Efficiency Summary
          </Typography>
          <Box mb={2}>
            <Typography variant="h4" color="primary">
              {data.reduce((acc, item) => acc + item.mpg, 0) / data.length} MPG
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Average MPG
            </Typography>
          </Box>
          <Box mb={2}>
            <Typography variant="h4" color="secondary">
              ${(data.reduce((acc, item) => acc + item.costPerMile, 0) / data.length).toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Avg Cost/Mile
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const CostAnalysisTab: React.FC<{ data: VehicleAnalyticsData['costPerMile'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Per Mile Analysis
          </Typography>
          <Box display="flex" alignItems="center" mb={2}>
            <Typography variant="h3" color="primary">
              ${data.current}
            </Typography>
            <Box ml={2}>
              <Typography variant="body2" color="text.secondary">
                Current Cost/Mile
              </Typography>
              <Box display="flex" alignItems="center">
                {data.trend === 'down' ? <TrendingDown color="success" /> : <TrendingUp color="error" />}
                <Typography variant="body2" color={data.trend === 'down' ? 'success.main' : 'error.main'}>
                  vs ${data.average} average
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Breakdown
          </Typography>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Fuel', value: data.breakdown.fuel, color: '#8884d8' },
                  { name: 'Maintenance', value: data.breakdown.maintenance, color: '#82ca9d' },
                  { name: 'Depreciation', value: data.breakdown.depreciation, color: '#ffc658' },
                  { name: 'Insurance', value: data.breakdown.insurance, color: '#ff7300' }
                ]}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                dataKey="value"
              >
                {[
                  { name: 'Fuel', value: data.breakdown.fuel, color: '#8884d8' },
                  { name: 'Maintenance', value: data.breakdown.maintenance, color: '#82ca9d' },
                  { name: 'Depreciation', value: data.breakdown.depreciation, color: '#ffc658' },
                  { name: 'Insurance', value: data.breakdown.insurance, color: '#ff7300' }
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <RechartsTooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const PeerComparisonTab: React.FC<{ data: VehicleAnalyticsData['peerComparison'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Peer Comparison (Anonymized)
          </Typography>
          <Box display="flex" justifyContent="space-around" alignItems="center" py={4}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary">
                ${data.yourCostPerMile}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Your Cost/Mile
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="text.secondary">
                ${data.peerAverage}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Peer Average
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                ${data.savings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                You Save/Mile
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="primary">
                {data.percentile}th
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Percentile
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const ROIAnalysisTab: React.FC<{ data: VehicleAnalyticsData['roiAnalysis'] }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            ROI Analysis
          </Typography>
          <Box mb={3}>
            <Typography variant="h3" color="primary">
              {data.roi}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Return on Investment
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Vehicle Investment:</Typography>
            <Typography>${data.vehicleInvestment.toLocaleString()}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Total Savings:</Typography>
            <Typography color="success.main">${data.totalSavings.toLocaleString()}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography>Payback Period:</Typography>
            <Typography>{data.paybackPeriod} years</Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recommendations
          </Typography>
          {data.recommendations.map((rec, index) => (
            <Box key={index} display="flex" alignItems="flex-start" mb={2}>
              <CheckCircle color="success" sx={{ mr: 1, mt: 0.5 }} />
              <Typography variant="body2">{rec}</Typography>
            </Box>
          ))}
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

export default VehicleAnalyticsDashboard;
