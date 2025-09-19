import React, { useState, useEffect } from 'react';
import { 
  Car, 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  Filter, 
  Download, 
  Upload,
  MapPin,
  Calendar,
  DollarSign,
  Users,
  Building2,
  BarChart3,
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
  trim?: string;
  vehicle_type: 'personal' | 'business' | 'fleet';
  business_use_percentage: number;
  primary_business_use?: string;
  department?: string;
  assigned_employee?: string;
  cost_center?: string;
  current_mileage: number;
  monthly_miles: number;
  business_miles_ytd: number;
  personal_miles_ytd: number;
  user_zipcode: string;
  assigned_msa?: string;
  purchase_price?: number;
  current_value?: number;
  monthly_payment?: number;
  insurance_cost_monthly?: number;
  tax_deduction_method?: string;
  depreciation_basis?: number;
  accumulated_depreciation?: number;
  created_date: string;
  updated_date: string;
}

interface MileageLog {
  id: number;
  fleet_vehicle_id: number;
  trip_date: string;
  start_location: string;
  end_location: string;
  purpose: string;
  business_use_type?: string;
  total_miles: number;
  business_miles: number;
  personal_miles: number;
  start_latitude?: number;
  start_longitude?: number;
  end_latitude?: number;
  end_longitude?: number;
  gps_verified: boolean;
  mileage_rate: number;
  business_deduction: number;
  receipt_attached: boolean;
  receipt_file_path?: string;
  created_date: string;
  updated_date: string;
}

const FleetManagementDashboard: React.FC = () => {
  const [vehicles, setVehicles] = useState<FleetVehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<FleetVehicle | null>(null);
  const [mileageLogs, setMileageLogs] = useState<MileageLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddVehicle, setShowAddVehicle] = useState(false);
  const [showMileageLog, setShowMileageLog] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterDepartment, setFilterDepartment] = useState('all');

  useEffect(() => {
    fetchFleetVehicles();
  }, []);

  const fetchFleetVehicles = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/professional/fleet');
      const data = await response.json();
      setVehicles(data.vehicles || []);
    } catch (error) {
      console.error('Error fetching fleet vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMileageLogs = async (vehicleId: number) => {
    try {
      const response = await fetch(`/api/professional/mileage/${vehicleId}`);
      const data = await response.json();
      setMileageLogs(data.mileage_logs || []);
    } catch (error) {
      console.error('Error fetching mileage logs:', error);
    }
  };

  const handleVehicleSelect = (vehicle: FleetVehicle) => {
    setSelectedVehicle(vehicle);
    fetchMileageLogs(vehicle.id);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getVehicleTypeColor = (type: string) => {
    switch (type) {
      case 'business': return 'bg-blue-100 text-blue-800';
      case 'personal': return 'bg-green-100 text-green-800';
      case 'fleet': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getBusinessUseColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredVehicles = vehicles.filter(vehicle => {
    const matchesSearch = 
      vehicle.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.vin.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || vehicle.vehicle_type === filterType;
    const matchesDepartment = filterDepartment === 'all' || vehicle.department === filterDepartment;
    
    return matchesSearch && matchesType && matchesDepartment;
  });

  const departments = [...new Set(vehicles.map(v => v.department).filter(Boolean))];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Fleet Management...</p>
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
              <Car className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Fleet Management</h1>
                <p className="text-gray-600">Manage your business vehicle fleet with unlimited vehicles</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setShowMileageLog(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2 inline" />
                Log Mileage
              </button>
              <button 
                onClick={() => setShowAddVehicle(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2 inline" />
                Add Vehicle
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Fleet List */}
          <div className="lg:col-span-2">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow mb-6">
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search vehicles..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Type</label>
                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="all">All Types</option>
                      <option value="business">Business</option>
                      <option value="personal">Personal</option>
                      <option value="fleet">Fleet</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Department</label>
                    <select
                      value={filterDepartment}
                      onChange={(e) => setFilterDepartment(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="all">All Departments</option>
                      {departments.map(dept => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Vehicle List */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  Fleet Vehicles ({filteredVehicles.length})
                </h3>
              </div>
              <div className="divide-y divide-gray-200">
                {filteredVehicles.map((vehicle) => (
                  <div
                    key={vehicle.id}
                    onClick={() => handleVehicleSelect(vehicle)}
                    className={`p-6 hover:bg-gray-50 cursor-pointer transition-colors ${
                      selectedVehicle?.id === vehicle.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-gray-100 rounded-lg">
                          <Car className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">
                            {vehicle.year} {vehicle.make} {vehicle.model}
                            {vehicle.trim && ` ${vehicle.trim}`}
                          </h4>
                          <p className="text-sm text-gray-500">VIN: {vehicle.vin}</p>
                          <div className="flex items-center space-x-4 mt-1">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getVehicleTypeColor(vehicle.vehicle_type)}`}>
                              {vehicle.vehicle_type}
                            </span>
                            {vehicle.department && (
                              <span className="text-xs text-gray-500">
                                <Building2 className="w-3 h-3 inline mr-1" />
                                {vehicle.department}
                              </span>
                            )}
                            {vehicle.assigned_employee && (
                              <span className="text-xs text-gray-500">
                                <Users className="w-3 h-3 inline mr-1" />
                                {vehicle.assigned_employee}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency((vehicle.monthly_payment || 0) + (vehicle.insurance_cost_monthly || 0))}/month
                        </div>
                        <div className={`text-sm ${getBusinessUseColor(vehicle.business_use_percentage)}`}>
                          {vehicle.business_use_percentage}% business use
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatNumber(vehicle.current_mileage)} miles
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Vehicle Details */}
          <div className="lg:col-span-1">
            {selectedVehicle ? (
              <div className="space-y-6">
                {/* Vehicle Info */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Vehicle Details</h3>
                  </div>
                  <div className="p-6 space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Vehicle Type</label>
                      <p className="text-sm text-gray-900 capitalize">{selectedVehicle.vehicle_type}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Business Use</label>
                      <p className="text-sm text-gray-900">{selectedVehicle.business_use_percentage}%</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Department</label>
                      <p className="text-sm text-gray-900">{selectedVehicle.department || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Assigned Employee</label>
                      <p className="text-sm text-gray-900">{selectedVehicle.assigned_employee || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Current Mileage</label>
                      <p className="text-sm text-gray-900">{formatNumber(selectedVehicle.current_mileage)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Monthly Miles</label>
                      <p className="text-sm text-gray-900">{formatNumber(selectedVehicle.monthly_miles)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Business Miles YTD</label>
                      <p className="text-sm text-gray-900">{formatNumber(selectedVehicle.business_miles_ytd)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Personal Miles YTD</label>
                      <p className="text-sm text-gray-900">{formatNumber(selectedVehicle.personal_miles_ytd)}</p>
                    </div>
                  </div>
                </div>

                {/* Financial Info */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Financial Details</h3>
                  </div>
                  <div className="p-6 space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Purchase Price</label>
                      <p className="text-sm text-gray-900">
                        {selectedVehicle.purchase_price ? formatCurrency(selectedVehicle.purchase_price) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Current Value</label>
                      <p className="text-sm text-gray-900">
                        {selectedVehicle.current_value ? formatCurrency(selectedVehicle.current_value) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Monthly Payment</label>
                      <p className="text-sm text-gray-900">
                        {selectedVehicle.monthly_payment ? formatCurrency(selectedVehicle.monthly_payment) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Insurance Cost</label>
                      <p className="text-sm text-gray-900">
                        {selectedVehicle.insurance_cost_monthly ? formatCurrency(selectedVehicle.insurance_cost_monthly) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Tax Deduction Method</label>
                      <p className="text-sm text-gray-900">
                        {selectedVehicle.tax_deduction_method || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
                  </div>
                  <div className="p-6 space-y-3">
                    <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                      <Edit className="w-4 h-4 mr-2 inline" />
                      Edit Vehicle
                    </button>
                    <button className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors">
                      <Plus className="w-4 h-4 mr-2 inline" />
                      Log Mileage
                    </button>
                    <button className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors">
                      <BarChart3 className="w-4 h-4 mr-2 inline" />
                      View Analytics
                    </button>
                    <button className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors">
                      <Trash2 className="w-4 h-4 mr-2 inline" />
                      Remove Vehicle
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <Car className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Vehicle</h3>
                <p className="text-gray-500">Choose a vehicle from the list to view details and manage it.</p>
              </div>
            )}
          </div>
        </div>

        {/* Mileage Logs */}
        {selectedVehicle && mileageLogs.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Mileage Logs</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trip</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Miles</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deduction</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">GPS</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {mileageLogs.slice(0, 10).map((log) => (
                    <tr key={log.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(log.trip_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>{log.start_location}</div>
                        <div className="text-gray-500">to {log.end_location}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.purpose}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.total_miles}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.business_miles}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(log.business_deduction)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.gps_verified ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <Clock className="w-4 h-4 text-gray-400" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FleetManagementDashboard;
