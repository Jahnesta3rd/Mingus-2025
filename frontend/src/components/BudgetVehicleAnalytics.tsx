import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Chip,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Timeline,
  AttachMoney,
  LocalGasStation,
  Build,
  TrendingUp,
  TrendingDown,
  Refresh,
  Upgrade,
  DirectionsCar
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface BudgetVehicleAnalyticsProps {
  className?: string;
  userTier: 'budget' | 'budget_career_vehicle';
}

interface BasicAnalyticsData {
  costTrends: Array<{
    date: string;
    totalCost: number;
    fuelCost: number;
    maintenanceCost: number;
  }>;
  fuelEfficiency: Array<{
    month: string;
    mpg: number;
    costPerMile: number;
  }>;
  monthlySummary: {
    totalSpent: number;
    fuelSpent: number;
    maintenanceSpent: number;
    averageMpg: number;
    costPerMile: number;
  };
}

const BudgetVehicleAnalytics: React.FC<BudgetVehicleAnalyticsProps> = ({
  className,
  userTier
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<BasicAnalyticsData | null>(null);
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);

  // Mock data for budget tier
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setData({
        costTrends: [
          { date: '2024-01', totalCost: 320, fuelCost: 180, maintenanceCost: 140 },
          { date: '2024-02', totalCost: 380, fuelCost: 200, maintenanceCost: 180 },
          { date: '2024-03', totalCost: 350, fuelCost: 170, maintenanceCost: 180 },
          { date: '2024-04', totalCost: 420, fuelCost: 220, maintenanceCost: 200 },
          { date: '2024-05', totalCost: 310, fuelCost: 180, maintenanceCost: 130 },
          { date: '2024-06', totalCost: 390, fuelCost: 210, maintenanceCost: 180 }
        ],
        fuelEfficiency: [
          { month: 'Jan', mpg: 26.5, costPerMile: 0.15 },
          { month: 'Feb', mpg: 27.2, costPerMile: 0.14 },
          { month: 'Mar', mpg: 25.8, costPerMile: 0.16 },
          { month: 'Apr', mpg: 28.1, costPerMile: 0.13 },
          { month: 'May', mpg: 26.9, costPerMile: 0.15 },
          { month: 'Jun', mpg: 27.5, costPerMile: 0.14 }
        ],
        monthlySummary: {
          totalSpent: 390,
          fuelSpent: 210,
          maintenanceSpent: 180,
          averageMpg: 27.0,
          costPerMile: 0.15
        }
      });
      setLoading(false);
    };

    fetchData();
  }, []);

  const handleUpgrade = () => {
    setUpgradeDialogOpen(true);
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

  return (
    <Box className={className}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" component="h1" gutterBottom>
            Vehicle Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Basic vehicle cost tracking and fuel efficiency monitoring
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <IconButton onClick={() => window.location.reload()}>
            <Refresh />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<Upgrade />}
            onClick={handleUpgrade}
            size="small"
          >
            Upgrade
          </Button>
        </Box>
      </Box>

      {/* Tier-specific notice */}
      <Alert severity="info" sx={{ mb: 3 }}>
        You're viewing basic vehicle analytics. Upgrade to Mid-tier ($35/month) for advanced features like peer comparison, ROI analysis, and detailed reporting.
      </Alert>

      {/* Monthly Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <AttachMoney color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Spent</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                ${data.monthlySummary.totalSpent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This Month
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <LocalGasStation color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">Fuel</Typography>
              </Box>
              <Typography variant="h4" color="secondary">
                ${data.monthlySummary.fuelSpent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This Month
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Build color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Maintenance</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                ${data.monthlySummary.maintenanceSpent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This Month
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <DirectionsCar color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Efficiency</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {data.monthlySummary.averageMpg} MPG
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Average
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Cost Trends Chart */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Cost Trends
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.costTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Line type="monotone" dataKey="totalCost" stroke="#8884d8" strokeWidth={2} name="Total Cost" />
                  <Line type="monotone" dataKey="fuelCost" stroke="#82ca9d" strokeWidth={2} name="Fuel" />
                  <Line type="monotone" dataKey="maintenanceCost" stroke="#ffc658" strokeWidth={2} name="Maintenance" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Fuel Efficiency Chart */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Fuel Efficiency Trends
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.fuelEfficiency}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="mpg" fill="#8884d8" name="MPG" />
                  <Line yAxisId="right" type="monotone" dataKey="costPerMile" stroke="#82ca9d" strokeWidth={2} name="Cost/Mile" />
                </BarChart>
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
                  {data.monthlySummary.averageMpg} MPG
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Average MPG
                </Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="h4" color="secondary">
                  ${data.monthlySummary.costPerMile}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cost per Mile
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Efficiency Trend
                </Typography>
                <Box display="flex" alignItems="center">
                  <TrendingUp color="success" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="success.main">
                    Improving
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Upgrade Dialog */}
      <Dialog open={upgradeDialogOpen} onClose={() => setUpgradeDialogOpen(false)}>
        <DialogTitle>Upgrade to Mid-tier</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Unlock advanced vehicle analytics features:
          </Typography>
          <Box component="ul" sx={{ pl: 2 }}>
            <li>Peer comparison with anonymized data</li>
            <li>ROI analysis for vehicle decisions</li>
            <li>Advanced maintenance predictions</li>
            <li>Detailed cost breakdowns</li>
            <li>Export functionality</li>
          </Box>
          <Typography variant="h6" color="primary" sx={{ mt: 2 }}>
            Only $35/month - Upgrade now!
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => {
            setUpgradeDialogOpen(false);
            // Handle upgrade logic
            window.location.href = '/pricing';
          }}>
            Upgrade Now
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BudgetVehicleAnalytics;
