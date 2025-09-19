import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  FileText, 
  Download, 
  Upload, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  DollarSign,
  MapPin,
  Calendar,
  BarChart3,
  Receipt,
  Car,
  Building2,
  Users,
  Clock,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';

interface TaxReport {
  id: number;
  fleet_vehicle_id: number;
  tax_year: number;
  report_type: string;
  report_period_start: string;
  report_period_end: string;
  total_business_miles: number;
  total_personal_miles: number;
  mileage_deduction_amount: number;
  average_mileage_rate: number;
  total_business_expenses: number;
  maintenance_expenses: number;
  fuel_expenses: number;
  insurance_expenses: number;
  depreciation_expenses: number;
  other_expenses: number;
  recommended_deduction_method: string;
  potential_savings: number;
  generated_date: string;
  report_file_path?: string;
  cpa_ready: boolean;
}

interface DeductionCalculation {
  mileage_method: {
    total_business_miles: number;
    mileage_rate: number;
    deduction_amount: number;
  };
  actual_expenses_method: {
    total_expenses: number;
    deduction_amount: number;
  };
  recommended_method: string;
  final_deduction: number;
  potential_tax_savings: number;
}

interface FleetVehicle {
  id: number;
  year: number;
  make: string;
  model: string;
  vehicle_type: string;
  business_use_percentage: number;
  business_miles_ytd: number;
  personal_miles_ytd: number;
}

const TaxOptimizationSuite: React.FC = () => {
  const [vehicles, setVehicles] = useState<FleetVehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<FleetVehicle | null>(null);
  const [taxReports, setTaxReports] = useState<TaxReport[]>([]);
  const [deductionCalculation, setDeductionCalculation] = useState<DeductionCalculation | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('calculator');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchVehicles();
    fetchTaxReports();
  }, []);

  const fetchVehicles = async () => {
    try {
      const response = await fetch('/api/professional/fleet');
      const data = await response.json();
      setVehicles(data.vehicles || []);
      if (data.vehicles && data.vehicles.length > 0) {
        setSelectedVehicle(data.vehicles[0]);
      }
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    }
  };

  const fetchTaxReports = async () => {
    try {
      // This would be a real API call
      setTaxReports([]);
    } catch (error) {
      console.error('Error fetching tax reports:', error);
    }
  };

  const calculateDeductions = async (vehicleId: number, taxYear: number) => {
    try {
      setLoading(true);
      const response = await fetch('/api/professional/tax/calculator', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fleet_vehicle_id: vehicleId,
          tax_year: taxYear
        })
      });
      const data = await response.json();
      setDeductionCalculation(data.deduction_calculation);
    } catch (error) {
      console.error('Error calculating deductions:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateTaxReport = async (vehicleId: number, taxYear: number, reportType: string) => {
    try {
      setLoading(true);
      const response = await fetch('/api/professional/tax/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fleet_vehicle_id: vehicleId,
          tax_year: taxYear,
          report_type: reportType
        })
      });
      const data = await response.json();
      if (data.success) {
        fetchTaxReports(); // Refresh reports
      }
    } catch (error) {
      console.error('Error generating tax report:', error);
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

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'mileage': return 'text-blue-600';
      case 'actual_expenses': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getMethodIcon = (method: string) => {
    switch (method) {
      case 'mileage': return <MapPin className="w-4 h-4" />;
      case 'actual_expenses': return <Receipt className="w-4 h-4" />;
      default: return <Calculator className="w-4 h-4" />;
    }
  };

  if (loading && !deductionCalculation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Tax Optimization Suite...</p>
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
              <Calculator className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Tax Optimization Suite</h1>
                <p className="text-gray-600">Maximize your business vehicle tax deductions with IRS-compliant reporting</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                <Download className="w-4 h-4 mr-2 inline" />
                Export All Reports
              </button>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                <Upload className="w-4 h-4 mr-2 inline" />
                Upload Receipts
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
              { id: 'calculator', name: 'Deduction Calculator', icon: Calculator },
              { id: 'reports', name: 'Tax Reports', icon: FileText },
              { id: 'mileage', name: 'Mileage Tracking', icon: MapPin },
              { id: 'expenses', name: 'Expense Management', icon: Receipt },
              { id: 'analytics', name: 'Tax Analytics', icon: BarChart3 }
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
        {activeTab === 'calculator' && (
          <div className="space-y-8">
            {/* Vehicle Selection */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Select Vehicle for Tax Calculation</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle</label>
                    <select
                      value={selectedVehicle?.id || ''}
                      onChange={(e) => {
                        const vehicle = vehicles.find(v => v.id === parseInt(e.target.value));
                        setSelectedVehicle(vehicle || null);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select a vehicle</option>
                      {vehicles.map(vehicle => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.year} {vehicle.make} {vehicle.model} ({vehicle.vehicle_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tax Year</label>
                    <select
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {[2024, 2023, 2022, 2021, 2020].map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => selectedVehicle && calculateDeductions(selectedVehicle.id, selectedYear)}
                    disabled={!selectedVehicle || loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Calculating...' : 'Calculate Deductions'}
                  </button>
                </div>
              </div>
            </div>

            {/* Deduction Calculation Results */}
            {deductionCalculation && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Mileage Method */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center">
                      <MapPin className="w-5 h-5 text-blue-600 mr-2" />
                      <h3 className="text-lg font-medium text-gray-900">Mileage Method</h3>
                    </div>
                  </div>
                  <div className="p-6 space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">Business Miles:</span>
                      <span className="text-sm text-gray-900">
                        {formatNumber(deductionCalculation.mileage_method.total_business_miles)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">Mileage Rate:</span>
                      <span className="text-sm text-gray-900">
                        {formatCurrency(deductionCalculation.mileage_method.mileage_rate)}/mile
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-4">
                      <span className="text-lg font-medium text-gray-900">Total Deduction:</span>
                      <span className="text-lg font-bold text-blue-600">
                        {formatCurrency(deductionCalculation.mileage_method.deduction_amount)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actual Expenses Method */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center">
                      <Receipt className="w-5 h-5 text-green-600 mr-2" />
                      <h3 className="text-lg font-medium text-gray-900">Actual Expenses Method</h3>
                    </div>
                  </div>
                  <div className="p-6 space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">Total Expenses:</span>
                      <span className="text-sm text-gray-900">
                        {formatCurrency(deductionCalculation.actual_expenses_method.total_expenses)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-4">
                      <span className="text-lg font-medium text-gray-900">Total Deduction:</span>
                      <span className="text-lg font-bold text-green-600">
                        {formatCurrency(deductionCalculation.actual_expenses_method.deduction_amount)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Recommendation */}
                <div className="lg:col-span-2 bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center">
                      <TrendingUp className="w-5 h-5 text-purple-600 mr-2" />
                      <h3 className="text-lg font-medium text-gray-900">Recommendation</h3>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center">
                        <div className={`p-2 rounded-lg mr-3 ${
                          deductionCalculation.recommended_method === 'mileage' ? 'bg-blue-100' : 'bg-green-100'
                        }`}>
                          {getMethodIcon(deductionCalculation.recommended_method)}
                        </div>
                        <div>
                          <h4 className="text-lg font-medium text-gray-900 capitalize">
                            {deductionCalculation.recommended_method.replace('_', ' ')} Method Recommended
                          </h4>
                          <p className="text-sm text-gray-600">
                            This method will provide the highest deduction for your vehicle
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900">
                          {formatCurrency(deductionCalculation.final_deduction)}
                        </div>
                        <div className="text-sm text-gray-600">Total Deduction</div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h5 className="text-sm font-medium text-gray-900">Potential Tax Savings</h5>
                          <p className="text-xs text-gray-600">Based on 25% tax bracket</p>
                        </div>
                        <div className="text-lg font-bold text-green-600">
                          {formatCurrency(deductionCalculation.potential_tax_savings)}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex space-x-4">
                      <button
                        onClick={() => selectedVehicle && generateTaxReport(selectedVehicle.id, selectedYear, 'annual')}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <FileText className="w-4 h-4 mr-2 inline" />
                        Generate Tax Report
                      </button>
                      <button className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
                        <Download className="w-4 h-4 mr-2 inline" />
                        Download Summary
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-gray-900">Tax Reports</h3>
                  <div className="flex space-x-4">
                    <select className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                      <option value="all">All Years</option>
                      <option value="2024">2024</option>
                      <option value="2023">2023</option>
                      <option value="2022">2022</option>
                    </select>
                    <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                      <FileText className="w-4 h-4 mr-2 inline" />
                      Generate New Report
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-6">
                {taxReports.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Tax Reports Generated</h3>
                    <p className="text-gray-500 mb-4">Generate your first tax report to get started with tax optimization.</p>
                    <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                      Generate Report
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {taxReports.map((report) => (
                      <div key={report.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className="p-2 bg-blue-100 rounded-lg">
                              <FileText className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                              <h4 className="text-sm font-medium text-gray-900">
                                {report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)} Report {report.tax_year}
                              </h4>
                              <p className="text-sm text-gray-500">
                                {new Date(report.report_period_start).toLocaleDateString()} - {new Date(report.report_period_end).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <div className="text-sm font-medium text-gray-900">
                                {formatCurrency(report.mileage_deduction_amount + report.total_business_expenses)}
                              </div>
                              <div className="text-xs text-gray-500">Total Deduction</div>
                            </div>
                            <div className="flex items-center space-x-2">
                              {report.cpa_ready && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  CPA Ready
                                </span>
                              )}
                              <button className="text-blue-600 hover:text-blue-800">
                                <Eye className="w-4 h-4" />
                              </button>
                              <button className="text-green-600 hover:text-green-800">
                                <Download className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Deductions</p>
                    <p className="text-2xl font-bold text-gray-900">$0</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <MapPin className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Business Miles</p>
                    <p className="text-2xl font-bold text-gray-900">0</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Tax Savings</p>
                    <p className="text-2xl font-bold text-gray-900">$0</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Tax Optimization Analytics</h3>
              </div>
              <div className="p-6">
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
                  <p className="text-gray-500">Advanced tax analytics and optimization insights will be available here.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaxOptimizationSuite;
