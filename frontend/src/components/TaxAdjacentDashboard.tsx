import React, { useState, useEffect } from 'react';
import { 
  Receipt, 
  MapPin, 
  FileText, 
  BookOpen, 
  BarChart3, 
  Plus, 
  Search, 
  Filter, 
  Download, 
  Upload,
  Calendar,
  DollarSign,
  Car,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  Users,
  Building2,
  Award
} from 'lucide-react';

interface ExpenseRecord {
  id: number;
  expense_date: string;
  category: string;
  subcategory?: string;
  description: string;
  amount: number;
  is_business_expense: boolean;
  business_percentage: number;
  business_purpose?: string;
  vendor_name?: string;
  receipt_attached: boolean;
  tax_year: number;
}

interface MileageLog {
  id: number;
  trip_date: string;
  start_location: string;
  end_location: string;
  trip_purpose: string;
  business_purpose?: string;
  total_miles: number;
  business_miles: number;
  personal_miles: number;
  odometer_start?: number;
  odometer_end?: number;
  gps_verified: boolean;
  business_use_percentage: number;
}

interface EducationalContent {
  id: number;
  title: string;
  content_type: string;
  category: string;
  description: string;
  reading_time_minutes?: number;
  difficulty_level?: string;
  is_irs_publication: boolean;
  irs_publication_number?: string;
  is_featured: boolean;
}

const TaxAdjacentDashboard: React.FC = () => {
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);
  const [mileageLogs, setMileageLogs] = useState<MileageLog[]>([]);
  const [educationalContent, setEducationalContent] = useState<EducationalContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch expenses
      const expensesResponse = await fetch(`/api/professional/expenses?tax_year=${selectedYear}`);
      const expensesData = await expensesResponse.json();
      setExpenses(expensesData.expenses || []);

      // Fetch mileage logs
      const mileageResponse = await fetch(`/api/professional/mileage?start_date=${selectedYear}-01-01&end_date=${selectedYear}-12-31`);
      const mileageData = await mileageResponse.json();
      setMileageLogs(mileageData.mileage_logs || []);

      // Fetch educational content
      const educationResponse = await fetch('/api/professional/education?featured=true&limit=6');
      const educationData = await educationResponse.json();
      setEducationalContent(educationData.content || []);

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      fuel: 'bg-blue-100 text-blue-800',
      maintenance: 'bg-green-100 text-green-800',
      insurance: 'bg-purple-100 text-purple-800',
      parking: 'bg-yellow-100 text-yellow-800',
      tolls: 'bg-orange-100 text-orange-800',
      registration: 'bg-red-100 text-red-800',
      repairs: 'bg-gray-100 text-gray-800',
      other: 'bg-indigo-100 text-indigo-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getPurposeColor = (purpose: string) => {
    const colors: { [key: string]: string } = {
      business_travel: 'bg-blue-100 text-blue-800',
      client_meeting: 'bg-green-100 text-green-800',
      office_commute: 'bg-purple-100 text-purple-800',
      business_errand: 'bg-orange-100 text-orange-800',
      personal: 'bg-gray-100 text-gray-800',
      other: 'bg-indigo-100 text-indigo-800'
    };
    return colors[purpose] || 'bg-gray-100 text-gray-800';
  };

  const getDifficultyColor = (difficulty: string) => {
    const colors: { [key: string]: string } = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-yellow-100 text-yellow-800',
      advanced: 'bg-red-100 text-red-800'
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  // Calculate summary statistics
  const totalExpenses = expenses.reduce((sum, expense) => sum + expense.amount, 0);
  const businessExpenses = expenses.filter(e => e.is_business_expense).reduce((sum, expense) => sum + expense.amount, 0);
  const personalExpenses = totalExpenses - businessExpenses;
  
  const totalMiles = mileageLogs.reduce((sum, log) => sum + log.total_miles, 0);
  const businessMiles = mileageLogs.reduce((sum, log) => sum + log.business_miles, 0);
  const personalMiles = mileageLogs.reduce((sum, log) => sum + log.personal_miles, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Tax-Adjacent Features...</p>
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
              <Receipt className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Tax-Adjacent Features</h1>
                <p className="text-gray-600">Expense tracking, documentation, and educational resources</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {[2024, 2023, 2022, 2021, 2020].map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                <Download className="w-4 h-4 mr-2 inline" />
                Export Report
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
              { id: 'expenses', name: 'Expense Tracking', icon: Receipt },
              { id: 'mileage', name: 'Mileage Logging', icon: MapPin },
              { id: 'maintenance', name: 'Maintenance Records', icon: Car },
              { id: 'education', name: 'Educational Resources', icon: BookOpen },
              { id: 'reports', name: 'Reports', icon: FileText }
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
                    <DollarSign className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Expenses</p>
                    <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalExpenses)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Building2 className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Business Expenses</p>
                    <p className="text-2xl font-bold text-gray-900">{formatCurrency(businessExpenses)}</p>
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
                    <p className="text-2xl font-bold text-gray-900">{formatNumber(businessMiles)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <FileText className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Receipts Attached</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {expenses.filter(e => e.receipt_attached).length}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Expenses */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Recent Expenses</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {expenses.slice(0, 5).map((expense) => (
                    <div key={expense.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(expense.category)}`}>
                            {expense.category}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{expense.description}</p>
                            <p className="text-sm text-gray-500">{formatDate(expense.expense_date)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900">{formatCurrency(expense.amount)}</p>
                          <p className="text-xs text-gray-500">
                            {expense.is_business_expense ? 'Business' : 'Personal'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Mileage */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Recent Mileage Logs</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {mileageLogs.slice(0, 5).map((log) => (
                    <div key={log.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPurposeColor(log.trip_purpose)}`}>
                            {log.trip_purpose.replace('_', ' ')}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {log.start_location} → {log.end_location}
                            </p>
                            <p className="text-sm text-gray-500">{formatDate(log.trip_date)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900">{log.business_miles} mi</p>
                          <p className="text-xs text-gray-500">
                            {log.gps_verified ? 'GPS Verified' : 'Manual Entry'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'expenses' && (
          <div className="space-y-6">
            {/* Expense Filters */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="">All Categories</option>
                    <option value="fuel">Fuel</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="insurance">Insurance</option>
                    <option value="parking">Parking</option>
                    <option value="tolls">Tolls</option>
                    <option value="registration">Registration</option>
                    <option value="repairs">Repairs</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="">All Types</option>
                    <option value="business">Business</option>
                    <option value="personal">Personal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-end">
                  <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                    <Search className="w-4 h-4 mr-2 inline" />
                    Filter
                  </button>
                </div>
              </div>
            </div>

            {/* Add Expense Button */}
            <div className="flex justify-end">
              <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                <Plus className="w-4 h-4 mr-2 inline" />
                Add Expense
              </button>
            </div>

            {/* Expenses Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Expense Records</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Receipt</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {expenses.map((expense) => (
                      <tr key={expense.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(expense.expense_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(expense.category)}`}>
                            {expense.category}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {expense.description}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(expense.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            expense.is_business_expense ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {expense.is_business_expense ? 'Business' : 'Personal'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {expense.receipt_attached ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-gray-400" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'education' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Educational Resources</h3>
                <p className="text-sm text-gray-600">Learn about vehicle tax deductions and IRS requirements</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {educationalContent.map((content) => (
                    <div key={content.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center">
                          <BookOpen className="w-5 h-5 text-blue-600 mr-2" />
                          <h4 className="text-sm font-medium text-gray-900">{content.title}</h4>
                        </div>
                        {content.is_featured && (
                          <Award className="w-4 h-4 text-yellow-500" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{content.description}</p>
                      <div className="flex items-center justify-between">
                        <div className="flex space-x-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDifficultyColor(content.difficulty_level || 'beginner')}`}>
                            {content.difficulty_level || 'beginner'}
                          </span>
                          {content.is_irs_publication && (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              IRS Publication
                            </span>
                          )}
                        </div>
                        {content.reading_time_minutes && (
                          <span className="text-xs text-gray-500">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {content.reading_time_minutes} min
                          </span>
                        )}
                      </div>
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

export default TaxAdjacentDashboard;
