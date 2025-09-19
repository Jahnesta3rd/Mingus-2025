import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Tooltip,
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
  Alert,
  CircularProgress,
  Divider,
  Switch,
  FormControlLabel,
  Badge,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab
} from '@mui/material';
import {
  Home,
  Work,
  AttachMoney,
  TrendingUp,
  TrendingDown,
  Star,
  StarBorder,
  Compare,
  Download,
  Share,
  Delete,
  CheckCircle,
  Warning,
  Info,
  ExpandMore,
  Timeline,
  Assessment,
  Business,
  LocationOn,
  Commute,
  Savings,
  AccountBalance,
  School,
  People,
  Security,
  Speed,
  DirectionsCar,
  Train,
  DirectionsWalk,
  LocalGasStation,
  Park,
  ShoppingCart,
  Restaurant,
  HealthAndSafety,
  School as SchoolIcon,
  Business as BusinessIcon,
  Assessment as AssessmentIcon,
  Insights,
  Upgrade,
  Lock
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
  ComposedChart,
  ScatterChart,
  Scatter
} from 'recharts';
import { useTierRestrictions, TierGate } from '../../hooks/useTierRestrictions';

// TypeScript Interfaces
interface HousingScenario {
  id: number;
  scenario_name: string;
  housing_data: {
    address: string;
    rent: number;
    bedrooms: number;
    bathrooms: number;
    square_feet: number;
    housing_type: string;
    amenities: string[];
    neighborhood: string;
    zip_code: string;
    latitude: number;
    longitude: number;
  };
  commute_data: {
    distance_miles: number;
    drive_time_minutes: number;
    public_transit_time_minutes: number;
    walking_time_minutes: number;
    gas_cost_daily: number;
    public_transit_cost_daily: number;
    parking_cost_daily: number;
    total_daily_cost: number;
    total_monthly_cost: number;
  };
  financial_impact: {
    affordability_score: number;
    rent_to_income_ratio: number;
    total_housing_cost: number;
    monthly_savings: number;
    annual_savings: number;
    cost_of_living_index: number;
    property_tax_estimate: number;
    insurance_estimate: number;
  };
  career_data: {
    job_opportunities_count: number;
    average_salary: number;
    salary_range_min: number;
    salary_range_max: number;
    industry_concentration: string[];
    remote_work_friendly: boolean;
    commute_impact_score: number;
  };
  is_favorite: boolean;
  created_at: string;
}

interface CurrentSituation {
  rent: number;
  commute_cost: number;
  total_monthly_cost: number;
  affordability_score: number;
  location: string;
  commute_time: number;
}

interface ScenarioComparisonData {
  current: CurrentSituation;
  scenarios: HousingScenario[];
  projections: {
    sixMonth: {
      current: number;
      scenarios: Array<{
        id: number;
        total_cost: number;
        savings: number;
        emergency_fund_impact: number;
      }>;
    };
    oneYear: {
      current: number;
      scenarios: Array<{
        id: number;
        total_cost: number;
        savings: number;
        emergency_fund_impact: number;
      }>;
    };
  };
  careerOpportunities: Array<{
    scenario_id: number;
    jobs: Array<{
      title: string;
      company: string;
      salary: number;
      distance: number;
      growth_potential: number;
      risk_level: 'low' | 'medium' | 'high';
    }>;
  }>;
}

interface ScenarioComparisonProps {
  className?: string;
  userTier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
  scenarios: HousingScenario[];
  currentSituation: CurrentSituation;
  onMakePrimary?: (scenarioId: number) => void;
  onExportAnalysis?: (scenarioId: number) => void;
  onShareScenario?: (scenarioId: number) => void;
  onDeleteScenario?: (scenarioId: number) => void;
  onToggleFavorite?: (scenarioId: number) => void;
}

const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({
  className,
  userTier,
  scenarios,
  currentSituation,
  onMakePrimary,
  onExportAnalysis,
  onShareScenario,
  onDeleteScenario,
  onToggleFavorite
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedScenarios, setSelectedScenarios] = useState<number[]>([]);
  const [comparisonData, setComparisonData] = useState<ScenarioComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('pdf');
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scenarioToDelete, setScenarioToDelete] = useState<number | null>(null);

  const { hasFeatureAccess, canPerformAction } = useTierRestrictions();

  // Mock data - in real implementation, this would come from API
  useEffect(() => {
    const fetchComparisonData = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setComparisonData({
        current: currentSituation,
        scenarios: scenarios,
        projections: {
          sixMonth: {
            current: currentSituation.total_monthly_cost * 6,
            scenarios: scenarios.map(scenario => ({
              id: scenario.id,
              total_cost: scenario.financial_impact.total_housing_cost * 6,
              savings: scenario.financial_impact.monthly_savings * 6,
              emergency_fund_impact: scenario.financial_impact.monthly_savings * 6 * 0.1
            }))
          },
          oneYear: {
            current: currentSituation.total_monthly_cost * 12,
            scenarios: scenarios.map(scenario => ({
              id: scenario.id,
              total_cost: scenario.financial_impact.total_housing_cost * 12,
              savings: scenario.financial_impact.monthly_savings * 12,
              emergency_fund_impact: scenario.financial_impact.monthly_savings * 12 * 0.1
            }))
          }
        },
        careerOpportunities: scenarios.map(scenario => ({
          scenario_id: scenario.id,
          jobs: [
            {
              title: 'Software Engineer',
              company: 'Tech Corp',
              salary: 85000,
              distance: 2.5,
              growth_potential: 85,
              risk_level: 'low' as const
            },
            {
              title: 'Product Manager',
              company: 'Startup Inc',
              salary: 95000,
              distance: 1.8,
              growth_potential: 90,
              risk_level: 'medium' as const
            }
          ]
        }))
      });
      setLoading(false);
    };

    fetchComparisonData();
  }, [scenarios, currentSituation]);

  const handleScenarioSelect = (scenarioId: number) => {
    setSelectedScenarios(prev => 
      prev.includes(scenarioId) 
        ? prev.filter(id => id !== scenarioId)
        : [...prev, scenarioId]
    );
  };

  const getMetricIndicator = (current: number, comparison: number, reverse = false) => {
    const isBetter = reverse ? comparison < current : comparison > current;
    return {
      icon: isBetter ? <TrendingUp color="success" /> : <TrendingDown color="error" />,
      color: isBetter ? 'success.main' : 'error.main',
      text: isBetter ? 'Better' : 'Worse'
    };
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getAffordabilityColor = (score: number) => {
    if (score >= 80) return 'success.main';
    if (score >= 60) return 'warning.main';
    return 'error.main';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'success.main';
      case 'medium': return 'warning.main';
      case 'high': return 'error.main';
      default: return 'text.secondary';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!comparisonData) {
    return (
      <Alert severity="error">
        Failed to load comparison data. Please try again.
      </Alert>
    );
  }

  return (
    <Box className={className}>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Scenario Comparison
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Compare your current situation with potential housing scenarios
        </Typography>
      </Box>

      {/* Scenario Overview Cards */}
      <Grid container spacing={3} mb={4}>
        {/* Current Situation Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', border: '2px solid', borderColor: 'primary.main' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Home color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Current Situation</Typography>
                <Chip label="Baseline" color="primary" size="small" sx={{ ml: 'auto' }} />
              </Box>
              
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  {currentSituation.location}
                </Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Monthly Cost
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(currentSituation.total_monthly_cost)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Affordability Score
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <Typography 
                      variant="h6" 
                      color={getAffordabilityColor(currentSituation.affordability_score)}
                    >
                      {currentSituation.affordability_score}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      /100
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Commute Time
                  </Typography>
                  <Typography variant="h6">
                    {currentSituation.commute_time} min
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Commute Cost
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(currentSituation.commute_cost)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Scenario Cards */}
        {scenarios.map((scenario) => {
          const rentIndicator = getMetricIndicator(
            currentSituation.total_monthly_cost, 
            scenario.financial_impact.total_housing_cost,
            true
          );
          const affordabilityIndicator = getMetricIndicator(
            currentSituation.affordability_score,
            scenario.financial_impact.affordability_score
          );

          return (
            <Grid item xs={12} md={4} key={scenario.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  border: selectedScenarios.includes(scenario.id) ? '2px solid' : '1px solid',
                  borderColor: selectedScenarios.includes(scenario.id) ? 'primary.main' : 'divider',
                  cursor: 'pointer'
                }}
                onClick={() => handleScenarioSelect(scenario.id)}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Home color="action" sx={{ mr: 1 }} />
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>
                      {scenario.scenario_name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleFavorite?.(scenario.id);
                      }}
                    >
                      {scenario.is_favorite ? <Star color="warning" /> : <StarBorder />}
                    </IconButton>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      {scenario.housing_data.address}
                    </Typography>
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Monthly Cost
                      </Typography>
                      <Box display="flex" alignItems="center">
                        <Typography variant="h6">
                          {formatCurrency(scenario.financial_impact.total_housing_cost)}
                        </Typography>
                        <Box ml={1}>
                          {rentIndicator.icon}
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Affordability Score
                      </Typography>
                      <Box display="flex" alignItems="center">
                        <Typography 
                          variant="h6" 
                          color={getAffordabilityColor(scenario.financial_impact.affordability_score)}
                        >
                          {scenario.financial_impact.affordability_score}
                        </Typography>
                        <Box ml={1}>
                          {affordabilityIndicator.icon}
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Commute Time
                      </Typography>
                      <Typography variant="h6">
                        {scenario.commute_data.drive_time_minutes} min
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Monthly Savings
                      </Typography>
                      <Typography 
                        variant="h6" 
                        color={scenario.financial_impact.monthly_savings > 0 ? 'success.main' : 'error.main'}
                      >
                        {formatCurrency(scenario.financial_impact.monthly_savings)}
                      </Typography>
                    </Grid>
                  </Grid>

                  {selectedScenarios.includes(scenario.id) && (
                    <Box mt={2}>
                      <Chip 
                        label="Selected for Comparison" 
                        color="primary" 
                        size="small" 
                        icon={<Compare />}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Tabs for Different Views */}
      <Box mb={3}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Financial Impact" icon={<AttachMoney />} />
          <Tab label="Comparison Table" icon={<Assessment />} />
          <TierGate feature="career_integration">
            <Tab label="Career Integration" icon={<Work />} />
          </TierGate>
        </Tabs>
      </Box>

      {/* Financial Impact Analysis */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* Monthly Cash Flow Chart */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Monthly Cash Flow Comparison
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    {
                      name: 'Current',
                      rent: currentSituation.rent,
                      commute: currentSituation.commute_cost,
                      total: currentSituation.total_monthly_cost
                    },
                    ...scenarios.map(scenario => ({
                      name: scenario.scenario_name,
                      rent: scenario.housing_data.rent,
                      commute: scenario.commute_data.total_monthly_cost,
                      total: scenario.financial_impact.total_housing_cost
                    }))
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Legend />
                    <Bar dataKey="rent" fill="#8884d8" name="Rent" />
                    <Bar dataKey="commute" fill="#82ca9d" name="Commute" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Projections */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Financial Projections
                </Typography>
                
                <Box mb={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    6-Month Projection
                  </Typography>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Current: {formatCurrency(comparisonData.projections.sixMonth.current)}
                    </Typography>
                    {scenarios.map(scenario => {
                      const projection = comparisonData.projections.sixMonth.scenarios.find(p => p.id === scenario.id);
                      return projection ? (
                        <Box key={scenario.id} display="flex" justifyContent="space-between">
                          <Typography variant="body2">
                            {scenario.scenario_name}:
                          </Typography>
                          <Typography variant="body2" color={projection.savings > 0 ? 'success.main' : 'error.main'}>
                            {formatCurrency(projection.total_cost)}
                          </Typography>
                        </Box>
                      ) : null;
                    })}
                  </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Box mb={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    1-Year Projection
                  </Typography>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Current: {formatCurrency(comparisonData.projections.oneYear.current)}
                    </Typography>
                    {scenarios.map(scenario => {
                      const projection = comparisonData.projections.oneYear.scenarios.find(p => p.id === scenario.id);
                      return projection ? (
                        <Box key={scenario.id} display="flex" justifyContent="space-between">
                          <Typography variant="body2">
                            {scenario.scenario_name}:
                          </Typography>
                          <Typography variant="body2" color={projection.savings > 0 ? 'success.main' : 'error.main'}>
                            {formatCurrency(projection.total_cost)}
                          </Typography>
                        </Box>
                      ) : null;
                    })}
                  </Box>
                </Box>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Emergency Fund Impact
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Potential additional savings for emergency fund
                  </Typography>
                  {scenarios.map(scenario => {
                    const projection = comparisonData.projections.oneYear.scenarios.find(p => p.id === scenario.id);
                    return projection ? (
                      <Box key={scenario.id} display="flex" justifyContent="space-between">
                        <Typography variant="body2">
                          {scenario.scenario_name}:
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          +{formatCurrency(projection.emergency_fund_impact)}
                        </Typography>
                      </Box>
                    ) : null;
                  })}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Comparison Table */}
      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Detailed Comparison
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Metric</TableCell>
                    <TableCell align="right">Current</TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        {scenario.scenario_name}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <Home sx={{ mr: 1 }} />
                        Rent
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(currentSituation.rent)}
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          {formatCurrency(scenario.housing_data.rent)}
                          <Box ml={1}>
                            {getMetricIndicator(
                              currentSituation.rent, 
                              scenario.housing_data.rent, 
                              true
                            ).icon}
                          </Box>
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <Commute sx={{ mr: 1 }} />
                        Commute Cost
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(currentSituation.commute_cost)}
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          {formatCurrency(scenario.commute_data.total_monthly_cost)}
                          <Box ml={1}>
                            {getMetricIndicator(
                              currentSituation.commute_cost, 
                              scenario.commute_data.total_monthly_cost, 
                              true
                            ).icon}
                          </Box>
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <AttachMoney sx={{ mr: 1 }} />
                        Total Monthly Cost
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="subtitle2">
                        {formatCurrency(currentSituation.total_monthly_cost)}
                      </Typography>
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          <Typography variant="subtitle2">
                            {formatCurrency(scenario.financial_impact.total_housing_cost)}
                          </Typography>
                          <Box ml={1}>
                            {getMetricIndicator(
                              currentSituation.total_monthly_cost, 
                              scenario.financial_impact.total_housing_cost, 
                              true
                            ).icon}
                          </Box>
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <Assessment sx={{ mr: 1 }} />
                        Affordability Score
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography 
                        variant="subtitle2" 
                        color={getAffordabilityColor(currentSituation.affordability_score)}
                      >
                        {currentSituation.affordability_score}/100
                      </Typography>
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          <Typography 
                            variant="subtitle2" 
                            color={getAffordabilityColor(scenario.financial_impact.affordability_score)}
                          >
                            {scenario.financial_impact.affordability_score}/100
                          </Typography>
                          <Box ml={1}>
                            {getMetricIndicator(
                              currentSituation.affordability_score,
                              scenario.financial_impact.affordability_score
                            ).icon}
                          </Box>
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <Timeline sx={{ mr: 1 }} />
                        Commute Time
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {currentSituation.commute_time} min
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          {scenario.commute_data.drive_time_minutes} min
                          <Box ml={1}>
                            {getMetricIndicator(
                              currentSituation.commute_time, 
                              scenario.commute_data.drive_time_minutes, 
                              true
                            ).icon}
                          </Box>
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">
                      <Box display="flex" alignItems="center">
                        <Savings sx={{ mr: 1 }} />
                        Monthly Savings
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography color="text.secondary">$0</Typography>
                    </TableCell>
                    {scenarios.map(scenario => (
                      <TableCell key={scenario.id} align="right">
                        <Typography 
                          color={scenario.financial_impact.monthly_savings > 0 ? 'success.main' : 'error.main'}
                        >
                          {formatCurrency(scenario.financial_impact.monthly_savings)}
                        </Typography>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Career Integration (Mid-tier+ only) */}
      {activeTab === 2 && hasFeatureAccess('career_integration') && (
        <Grid container spacing={3}>
          {comparisonData.careerOpportunities.map((careerData) => {
            const scenario = scenarios.find(s => s.id === careerData.scenario_id);
            if (!scenario) return null;

            return (
              <Grid item xs={12} md={6} key={careerData.scenario_id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Career Opportunities - {scenario.scenario_name}
                    </Typography>
                    
                    <Box mb={2}>
                      <Typography variant="body2" color="text.secondary">
                        {scenario.career_data.job_opportunities_count} opportunities within 30 miles
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average salary: {formatCurrency(scenario.career_data.average_salary)}
                      </Typography>
                    </Box>

                    <List>
                      {careerData.jobs.map((job, index) => (
                        <ListItem key={index} divider={index < careerData.jobs.length - 1}>
                          <ListItemIcon>
                            <Work />
                          </ListItemIcon>
                          <ListItemText
                            primary={job.title}
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  {job.company} • {formatCurrency(job.salary)} • {job.distance} miles
                                </Typography>
                                <Box display="flex" alignItems="center" mt={1}>
                                  <Chip 
                                    label={`${job.growth_potential}% growth potential`}
                                    size="small"
                                    color="primary"
                                    sx={{ mr: 1 }}
                                  />
                                  <Chip 
                                    label={job.risk_level}
                                    size="small"
                                    sx={{ 
                                      color: getRiskColor(job.risk_level),
                                      borderColor: getRiskColor(job.risk_level)
                                    }}
                                    variant="outlined"
                                  />
                                </Box>
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>

                    <Box mt={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        Career Growth Projections (2-5 years)
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={scenario.career_data.commute_impact_score} 
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Commute Impact Score: {scenario.career_data.commute_impact_score}/100
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Upgrade Prompt for Career Integration */}
      {activeTab === 2 && !hasFeatureAccess('career_integration') && (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <Lock color="disabled" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Career Integration Available in Mid-tier+
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Unlock job opportunity analysis, salary comparisons, and career growth projections
                to make informed decisions about your housing location.
              </Typography>
              <Button variant="contained" startIcon={<Upgrade />}>
                Upgrade to Mid-tier
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Box mt={4} display="flex" gap={2} flexWrap="wrap">
        {selectedScenarios.length > 0 && (
          <Button
            variant="contained"
            startIcon={<CheckCircle />}
            onClick={() => {
              if (selectedScenarios.length === 1) {
                onMakePrimary?.(selectedScenarios[0]);
              }
            }}
            disabled={selectedScenarios.length !== 1}
          >
            Make Primary Choice
          </Button>
        )}

        <TierGate 
          feature="export_functionality"
          fallback={
            <Tooltip title="Export functionality available in Professional tier">
              <span>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  disabled
                >
                  Export Analysis
                </Button>
              </span>
            </Tooltip>
          }
        >
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => setExportDialogOpen(true)}
            disabled={selectedScenarios.length === 0}
          >
            Export Analysis
          </Button>
        </TierGate>

        <Button
          variant="outlined"
          startIcon={<Share />}
          onClick={() => setShareDialogOpen(true)}
          disabled={selectedScenarios.length === 0}
        >
          Share Scenario
        </Button>

        {selectedScenarios.length > 0 && (
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={() => {
              if (selectedScenarios.length === 1) {
                setScenarioToDelete(selectedScenarios[0]);
                setDeleteDialogOpen(true);
              }
            }}
            disabled={selectedScenarios.length !== 1}
          >
            Delete Scenario
          </Button>
        )}
      </Box>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Analysis</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            Select export format for your scenario comparison:
          </Typography>
          <Box mt={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={exportFormat === 'pdf'}
                  onChange={(e) => setExportFormat(e.target.checked ? 'pdf' : 'excel')}
                />
              }
              label="PDF Report"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={exportFormat === 'excel'}
                  onChange={(e) => setExportFormat(e.target.checked ? 'excel' : 'pdf')}
                />
              }
              label="Excel Spreadsheet"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              onExportAnalysis?.(selectedScenarios[0]);
              setExportDialogOpen(false);
            }}
          >
            Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)}>
        <DialogTitle>Share Scenario</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            Share your housing scenario analysis with others:
          </Typography>
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary">
              Selected scenarios: {selectedScenarios.map(id => 
                scenarios.find(s => s.id === id)?.scenario_name
              ).join(', ')}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              selectedScenarios.forEach(id => onShareScenario?.(id));
              setShareDialogOpen(false);
            }}
          >
            Share
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Scenario</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Are you sure you want to delete this scenario? This action cannot be undone.
          </Typography>
          {scenarioToDelete && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Scenario: {scenarios.find(s => s.id === scenarioToDelete)?.scenario_name}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={() => {
              if (scenarioToDelete) {
                onDeleteScenario?.(scenarioToDelete);
                setDeleteDialogOpen(false);
                setScenarioToDelete(null);
              }
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScenarioComparison;
