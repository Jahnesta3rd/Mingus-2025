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
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
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
  DirectionsCar,
  Business,
  AccountBalance,
  ExpandMore,
  FilterList,
  GetApp
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
  ComposedChart,
  Heatmap
} from 'recharts';

interface ProfessionalVehicleAnalyticsProps {
  className?: string;
}

interface ProfessionalAnalyticsData {
  costTrends: Array<{
    date: string;
    totalCost: number;
    fuelCost: number;
    maintenanceCost: number;
    insuranceCost: number;
    otherCost: number;
    businessCost: number;
    personalCost: number;
  }>;
  maintenanceAccuracy: {
    predicted: number;
    actual: number;
    accuracy: number;
    savings: number;
    predictions: Array<{
      date: string;
      predicted: number;
      actual: number;
      variance: number;
    }>;
  };
  fuelEfficiency: Array<{
    month: string;
    mpg: number;
    costPerMile: number;
    totalMiles: number;
    fuelCost: number;
    businessMiles: number;
    personalMiles: number;
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
    businessVsPersonal: {
      business: number;
      personal: number;
      taxSavings: number;
    };
  };
  peerComparison: {
    yourCostPerMile: number;
    peerAverage: number;
    percentile: number;
    savings: number;
    industryBenchmark: number;
    regionalBenchmark: number;
  };
  roiAnalysis: {
    vehicleInvestment: number;
    totalSavings: number;
    roi: number;
    paybackPeriod: number;
    taxBenefits: number;
    recommendations: string[];
    fleetOptimization: {
      optimalFleetSize: number;
      currentFleetSize: number;
      potentialSavings: number;
    };
  };
  businessMetrics: {
    totalBusinessMiles: number;
    totalPersonalMiles: number;
    businessUsePercentage: number;
    taxDeductionAmount: number;
    irsComplianceScore: number;
  };
  exportData?: any;
}

const ProfessionalVehicleAnalytics: React.FC<ProfessionalVehicleAnalyticsProps> = ({
  className
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ProfessionalAnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState('6months');
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');
  const [filterDialogOpen, setFilterDialogOpen] = useState(false);

  // Mock data for professional tier
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setData({
        costTrends: [
          { date: '2024-01', totalCost: 850, fuelCost: 300, maintenanceCost: 250, insuranceCost: 150, otherCost: 50, businessCost: 600, personalCost: 250 },
          { date: '2024-02', totalCost: 920, fuelCost: 320, maintenanceCost: 300, insuranceCost: 150, otherCost: 50, businessCost: 650, personalCost: 270 },
          { date: '2024-03', totalCost: 880, fuelCost: 280, maintenanceCost: 350, insuranceCost: 150, otherCost: 0, businessCost: 620, personalCost: 260 },
          { date: '2024-04', totalCost: 1000, fuelCost: 350, maintenanceCost: 400, insuranceCost: 150, otherCost: 50, businessCost: 700, personalCost: 300 },
          { date: '2024-05', totalCost: 820, fuelCost: 300, maintenanceCost: 220, insuranceCost: 150, otherCost: 50, businessCost: 580, personalCost: 240 },
          { date: '2024-06', totalCost: 950, fuelCost: 330, maintenanceCost: 300, insuranceCost: 150, otherCost: 70, businessCost: 670, personalCost: 280 }
        ],
        maintenanceAccuracy: {
          predicted: 2400,
          actual: 2300,
          accuracy: 95.8,
          savings: 100,
          predictions: [
            { date: '2024-01', predicted: 400, actual: 380, variance: -5 },
            { date: '2024-02', predicted: 500, actual: 520, variance: 4 },
            { date: '2024-03', predicted: 600, actual: 580, variance: -3.3 },
            { date: '2024-04', predicted: 450, actual: 460, variance: 2.2 },
            { date: '2024-05', predicted: 350, actual: 340, variance: -2.9 },
            { date: '2024-06', predicted: 500, actual: 480, variance: -4 }
          ]
        },
        fuelEfficiency: [
          { month: 'Jan', mpg: 28.5, costPerMile: 0.12, totalMiles: 2500, fuelCost: 300, businessMiles: 1800, personalMiles: 700 },
          { month: 'Feb', mpg: 29.2, costPerMile: 0.11, totalMiles: 2300, fuelCost: 320, businessMiles: 1650, personalMiles: 650 },
          { month: 'Mar', mpg: 27.8, costPerMile: 0.13, totalMiles: 2700, fuelCost: 280, businessMiles: 1950, personalMiles: 750 },
          { month: 'Apr', mpg: 30.1, costPerMile: 0.10, totalMiles: 2000, fuelCost: 350, businessMiles: 1400, personalMiles: 600 },
          { month: 'May', mpg: 28.9, costPerMile: 0.12, totalMiles: 2400, fuelCost: 300, businessMiles: 1700, personalMiles: 700 },
          { month: 'Jun', mpg: 29.5, costPerMile: 0.11, totalMiles: 2200, fuelCost: 330, businessMiles: 1600, personalMiles: 600 }
        ],
        costPerMile: {
          current: 0.42,
          average: 0.45,
          trend: 'down',
          breakdown: {
            fuel: 0.12,
            maintenance: 0.15,
            depreciation: 0.10,
            insurance: 0.05
          },
          businessVsPersonal: {
            business: 0.35,
            personal: 0.55,
            taxSavings: 0.08
          }
        },
        peerComparison: {
          yourCostPerMile: 0.42,
          peerAverage: 0.48,
          percentile: 20,
          savings: 0.06,
          industryBenchmark: 0.45,
          regionalBenchmark: 0.50
        },
        roiAnalysis: {
          vehicleInvestment: 75000,
          totalSavings: 12000,
          roi: 16.0,
          paybackPeriod: 6.25,
          taxBenefits: 3500,
          recommendations: [
            'Optimize fleet size based on usage patterns',
            'Implement predictive maintenance scheduling',
            'Consider electric vehicles for high-mileage routes',
            'Review insurance coverage for better rates',
            'Implement driver training for fuel efficiency'
          ],
          fleetOptimization: {
            optimalFleetSize: 3,
            currentFleetSize: 4,
            potentialSavings: 2500
          }
        },
        businessMetrics: {
          totalBusinessMiles: 12000,
          totalPersonalMiles: 4000,
          businessUsePercentage: 75,
          taxDeductionAmount: 4500,
          irsComplianceScore: 95
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
    setExportDialogOpen(true);
  };

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
    { label: 'Executive Summary', icon: <Dashboard /> },
    { label: 'Cost Analysis', icon: <AttachMoney /> },
    { label: 'Fleet Management', icon: <DirectionsCar /> },
    { label: 'Tax Optimization', icon: <AccountBalance /> },
    { label: 'Peer Benchmarking', icon: <GitCompare /> },
    { label: 'ROI & Strategy', icon: <Assessment /> },
    { label: 'Compliance', icon: <CheckCircle /> }
  ];

  return (
    <Box className={className}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Professional Vehicle Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Advanced fleet management and business optimization insights
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
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => setFilterDialogOpen(true)}
          >
            Filters
          </Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={handleExport}
          >
            Export Data
          </Button>
          <IconButton onClick={() => window.location.reload()}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Professional tier badge */}
      <Alert severity="success" sx={{ mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Professional Tier Active
            </Typography>
            <Typography variant="body2">
              Full access to advanced analytics, export functionality, and business optimization tools
            </Typography>
          </Box>
          <Chip label="Professional" color="success" />
        </Box>
      </Alert>

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
        {activeTab === 0 && <ExecutiveSummaryTab data={data} />}
        {activeTab === 1 && <CostAnalysisTab data={data} />}
        {activeTab === 2 && <FleetManagementTab data={data} />}
        {activeTab === 3 && <TaxOptimizationTab data={data} />}
        {activeTab === 4 && <PeerBenchmarkingTab data={data} />}
        {activeTab === 5 && <ROIStrategyTab data={data} />}
        {activeTab === 6 && <ComplianceTab data={data} />}
      </Box>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)} maxWidth="sm" fullWidth>
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
              <MenuItem value="excel">Excel Workbook</MenuItem>
              <MenuItem value="pdf">PDF Report</MenuItem>
              <MenuItem value="json">JSON Data</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Data Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Data Range"
            >
              <MenuItem value="3months">3 Months</MenuItem>
              <MenuItem value="6months">6 Months</MenuItem>
              <MenuItem value="1year">1 Year</MenuItem>
              <MenuItem value="2years">2 Years</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => {
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
const ExecutiveSummaryTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Total Investment
          </Typography>
          <Typography variant="h3" color="primary">
            ${data.roiAnalysis.vehicleInvestment.toLocaleString()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Fleet Value
          </Typography>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            ROI
          </Typography>
          <Typography variant="h3" color="success.main">
            {data.roiAnalysis.roi}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Return on Investment
          </Typography>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tax Benefits
          </Typography>
          <Typography variant="h3" color="info.main">
            ${data.roiAnalysis.taxBenefits.toLocaleString()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Annual Savings
          </Typography>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Compliance Score
          </Typography>
          <Typography variant="h3" color="warning.main">
            {data.businessMetrics.irsComplianceScore}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            IRS Compliance
          </Typography>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const CostAnalysisTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Business vs Personal Cost Breakdown
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={data.costTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Area type="monotone" dataKey="totalCost" stackId="1" stroke="#8884d8" fill="#8884d8" />
              <Bar dataKey="businessCost" stackId="2" fill="#82ca9d" />
              <Bar dataKey="personalCost" stackId="2" fill="#ffc658" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const FleetManagementTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Fleet Optimization
          </Typography>
          <Box mb={2}>
            <Typography variant="h4" color="primary">
              {data.roiAnalysis.fleetOptimization.optimalFleetSize}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Optimal Fleet Size
            </Typography>
          </Box>
          <Box mb={2}>
            <Typography variant="h4" color="secondary">
              {data.roiAnalysis.fleetOptimization.currentFleetSize}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Current Fleet Size
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="success.main">
              ${data.roiAnalysis.fleetOptimization.potentialSavings.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Potential Annual Savings
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Business Use Analysis
          </Typography>
          <Box mb={2}>
            <Typography variant="h4" color="primary">
              {data.businessMetrics.businessUsePercentage}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Business Use Percentage
            </Typography>
          </Box>
          <Box mb={2}>
            <Typography variant="h4" color="secondary">
              {data.businessMetrics.totalBusinessMiles.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Business Miles
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="success.main">
              ${data.businessMetrics.taxDeductionAmount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Tax Deduction Amount
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const TaxOptimizationTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tax Optimization Summary
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Metric</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell align="right">Tax Benefit</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Business Miles</TableCell>
                  <TableCell align="right">{data.businessMetrics.totalBusinessMiles.toLocaleString()}</TableCell>
                  <TableCell align="right">${(data.businessMetrics.totalBusinessMiles * 0.655).toFixed(0)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Vehicle Depreciation</TableCell>
                  <TableCell align="right">${data.roiAnalysis.vehicleInvestment.toLocaleString()}</TableCell>
                  <TableCell align="right">${(data.roiAnalysis.vehicleInvestment * 0.2).toFixed(0)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Total Tax Benefits</TableCell>
                  <TableCell align="right">-</TableCell>
                  <TableCell align="right">${data.roiAnalysis.taxBenefits.toLocaleString()}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

const PeerBenchmarkingTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Industry Benchmarking
          </Typography>
          <Box display="flex" justifyContent="space-around" alignItems="center" py={4}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary">
                ${data.peerComparison.yourCostPerMile}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Your Cost/Mile
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="text.secondary">
                ${data.peerComparison.peerAverage}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Peer Average
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="info.main">
                ${data.peerComparison.industryBenchmark}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Industry Benchmark
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                {data.peerComparison.percentile}th
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

const ROIStrategyTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            ROI Analysis
          </Typography>
          <Box mb={3}>
            <Typography variant="h3" color="primary">
              {data.roiAnalysis.roi}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Return on Investment
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Vehicle Investment:</Typography>
            <Typography>${data.roiAnalysis.vehicleInvestment.toLocaleString()}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography>Total Savings:</Typography>
            <Typography color="success.main">${data.roiAnalysis.totalSavings.toLocaleString()}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Typography>Payback Period:</Typography>
            <Typography>{data.roiAnalysis.paybackPeriod} years</Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Strategic Recommendations
          </Typography>
          {data.roiAnalysis.recommendations.map((rec, index) => (
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

const ComplianceTab: React.FC<{ data: ProfessionalAnalyticsData }> = ({ data }) => (
  <Grid container spacing={3}>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            IRS Compliance Dashboard
          </Typography>
          <Box display="flex" alignItems="center" mb={3}>
            <Typography variant="h3" color="success.main">
              {data.businessMetrics.irsComplianceScore}%
            </Typography>
            <Box ml={2}>
              <Typography variant="body2" color="text.secondary">
                Compliance Score
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={data.businessMetrics.irsComplianceScore} 
                sx={{ height: 8, borderRadius: 4, mt: 1 }}
              />
            </Box>
          </Box>
          <Alert severity="success">
            Your vehicle expense tracking meets IRS requirements for business use documentation.
          </Alert>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

export default ProfessionalVehicleAnalytics;
