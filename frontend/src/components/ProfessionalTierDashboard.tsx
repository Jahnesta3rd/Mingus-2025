import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Car, 
  Calculator, 
  BarChart3, 
  FileText, 
  CreditCard, 
  Users, 
  Shield,
  TrendingUp,
  DollarSign,
  MapPin,
  Calendar,
  Settings,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface FleetVehicle {
  id: number;
  vin: string;
  year: number;
  make: string;
  model: string;
  vehicle_type: 'personal' | 'business' | 'fleet';
  business_use_percentage: number;
  department?: string;
  assigned_employee?: string;
  current_mileage: number;
  monthly_miles: number;
  business_miles_ytd: number;
  personal_miles_ytd: number;
  purchase_price?: number;
  monthly_payment?: number;
  insurance_cost_monthly?: number;
}

interface FleetAnalytics {
  total_vehicles: number;
  business_vehicles: number;
  personal_vehicles: number;
  total_monthly_cost: number;
  cost_per_mile: number;
  total_miles: number;
  business_miles: number;
  personal_miles: number;
  maintenance_cost_total: number;
  total_tax_deductions: number;
}

interface IntegrationStatus {
  quickbooks: {
    connected: boolean;
    last_sync: string;
    sync_status: string;
    expenses_synced: number;
  };
  credit_card: {
    connected: boolean;
    last_sync: string;
    sync_status: string;
    transactions_categorized: number;
  };
  hr_system: {
    connected: boolean;
    last_sync: string;
    sync_status: string;
    employees_synced: number;
  };
  insurance: {
    connected: boolean;
    last_sync: string;
    sync_status: string;
    policies_synced: number;
  };
}

const ProfessionalTierDashboard: React.FC = () => {
  const [fleetVehicles, setFleetVehicles] = useState<FleetVehicle[]>([]);
  const [analytics, setAnalytics] = useState<FleetAnalytics | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch fleet vehicles
      const vehiclesResponse = await fetch('/api/professional/fleet');
      const vehiclesData = await vehiclesResponse.json();
      setFleetVehicles(vehiclesData.vehicles || []);

      // Fetch analytics
      const analyticsResponse = await fetch('/api/professional/analytics/fleet');
      const analyticsData = await analyticsResponse.json();
      setAnalytics(analyticsData.analytics);

      // Fetch integration status
      const integrationResponse = await fetch('/api/professional/integrations/status');
      const integrationData = await integrationResponse.json();
      setIntegrationStatus(integrationData.integrations);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getVehicleTypeColor = (type: string) => {
    switch (type) {
      case 'business': return 'bg-blue-100 text-blue-800';
      case 'personal': return 'bg-green-100 text-green-800';
      case 'fleet': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getIntegrationStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Professional Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Building2 className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Professional Fleet Management</h1>
                <p className="text-gray-600">Executive-level vehicle cost management and optimization</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                <Download className="w-4 h-4 mr-2 inline" />
                Export Report
              </button>
              <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                <Settings className="w-4 h-4 mr-2 inline" />
                Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'fleet', name: 'Fleet Management', icon: Car },
              { id: 'tax', name: 'Tax Optimization', icon: Calculator },
              { id: 'analytics', name: 'Analytics', icon: TrendingUp },
              { id: 'integrations', name: 'Integrations', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Car className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Vehicles</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics?.total_vehicles || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Monthly Cost</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(analytics?.total_monthly_cost || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <MapPin className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Business Miles</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(analytics?.business_miles || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Calculator className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Tax Deductions</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(analytics?.total_tax_deductions || 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Fleet Overview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Fleet Overview</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Vehicle Distribution</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Business Vehicles</span>
                        <span className="text-sm font-medium">{analytics?.business_vehicles || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Personal Vehicles</span>
                        <span className="text-sm font-medium">{analytics?.personal_vehicles || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Fleet Vehicles</span>
                        <span className="text-sm font-medium">{(analytics?.total_vehicles || 0) - (analytics?.business_vehicles || 0) - (analytics?.personal_vehicles || 0)}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Cost Analysis</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Cost per Mile</span>
                        <span className="text-sm font-medium">{formatCurrency(analytics?.cost_per_mile || 0)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Maintenance Cost</span>
                        <span className="text-sm font-medium">{formatCurrency(analytics?.maintenance_cost_total || 0)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Miles</span>
                        <span className="text-sm font-medium">{formatNumber(analytics?.total_miles || 0)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Vehicles */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Fleet Vehicles</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vehicle</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business Use</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monthly Cost</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {fleetVehicles.slice(0, 5).map((vehicle) => (
                      <tr key={vehicle.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {vehicle.year} {vehicle.make} {vehicle.model}
                          </div>
                          <div className="text-sm text-gray-500">VIN: {vehicle.vin}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getVehicleTypeColor(vehicle.vehicle_type)}`}>
                            {vehicle.vehicle_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {vehicle.department || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {vehicle.business_use_percentage}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency((vehicle.monthly_payment || 0) + (vehicle.insurance_cost_monthly || 0))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'integrations' && integrationStatus && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Business Integrations</h3>
                <p className="text-sm text-gray-600">Connect your business systems for seamless data flow</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(integrationStatus).map(([key, integration]) => (
                    <div key={key} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          {key === 'quickbooks' && <FileText className="w-5 h-5 text-blue-600 mr-2" />}
                          {key === 'credit_card' && <CreditCard className="w-5 h-5 text-green-600 mr-2" />}
                          {key === 'hr_system' && <Users className="w-5 h-5 text-purple-600 mr-2" />}
                          {key === 'insurance' && <Shield className="w-5 h-5 text-red-600 mr-2" />}
                          <h4 className="text-sm font-medium text-gray-900 capitalize">
                            {key.replace('_', ' ')}
                          </h4>
                        </div>
                        {getIntegrationStatusIcon(integration.sync_status)}
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Status:</span>
                          <span className={integration.connected ? 'text-green-600' : 'text-red-600'}>
                            {integration.connected ? 'Connected' : 'Disconnected'}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Last Sync:</span>
                          <span className="text-gray-900">
                            {new Date(integration.last_sync).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Items Synced:</span>
                          <span className="text-gray-900">
                            {Object.values(integration)[3] || 0}
                          </span>
                        </div>
                      </div>
                      <button className="mt-3 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm">
                        {integration.connected ? 'Manage' : 'Connect'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfessionalTierDashboard;
