import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calendar, 
  Car, 
  AlertTriangle, 
  CheckCircle, 
  BarChart3,
  PieChart,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  Filter,
  Download
} from 'lucide-react';

// Types
interface MonthlyMaintenanceCost {
  month: string;
  totalCost: number;
  routineCost: number;
  majorRepairCost: number;
  services: string[];
  isProjected: boolean;
}

interface CashFlowIntegrationProps {
  vehicleId?: string;
  className?: string;
  onViewDetails?: (month: string) => void;
}

const MaintenanceCashFlowIntegration: React.FC<CashFlowIntegrationProps> = ({
  vehicleId,
  className = '',
  onViewDetails
}) => {
  const [monthlyCosts, setMonthlyCosts] = useState<MonthlyMaintenanceCost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'chart' | 'list'>('chart');

  // Mock data for demonstration
  const mockMonthlyCosts: MonthlyMaintenanceCost[] = [
    {
      month: '2024-02',
      totalCost: 120.99,
      routineCost: 120.99,
      majorRepairCost: 0,
      services: ['Oil Change', 'Tire Rotation'],
      isProjected: false
    },
    {
      month: '2024-03',
      totalCost: 189.99,
      routineCost: 0,
      majorRepairCost: 189.99,
      services: ['Brake Pad Replacement'],
      isProjected: true
    },
    {
      month: '2024-04',
      totalCost: 299.99,
      routineCost: 0,
      majorRepairCost: 299.99,
      services: ['Transmission Service'],
      isProjected: true
    },
    {
      month: '2024-05',
      totalCost: 425.00,
      routineCost: 0,
      majorRepairCost: 425.00,
      services: ['Engine Tune-up'],
      isProjected: true
    },
    {
      month: '2024-06',
      totalCost: 25.00,
      routineCost: 25.00,
      majorRepairCost: 0,
      services: ['Tire Rotation'],
      isProjected: true
    },
    {
      month: '2024-07',
      totalCost: 0,
      routineCost: 0,
      majorRepairCost: 0,
      services: [],
      isProjected: true
    },
    {
      month: '2024-08',
      totalCost: 3500.00,
      routineCost: 0,
      majorRepairCost: 3500.00,
      services: ['Transmission Replacement'],
      isProjected: true
    }
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setMonthlyCosts(mockMonthlyCosts);
        setError(null);
      } catch (err) {
        setError('Failed to load cash flow data');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [vehicleId]);

  const totalProjectedCost = monthlyCosts.reduce((sum, month) => sum + month.totalCost, 0);
  const averageMonthlyCost = monthlyCosts.length > 0 ? totalProjectedCost / monthlyCosts.length : 0;
  const highestMonth = monthlyCosts.reduce((max, month) => 
    month.totalCost > max.totalCost ? month : max, monthlyCosts[0] || { totalCost: 0 }
  );

  const formatMonth = (monthString: string) => {
    const date = new Date(monthString + '-01');
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getCostColor = (cost: number, isProjected: boolean) => {
    if (cost === 0) return 'text-gray-400';
    if (cost > 1000) return 'text-red-400';
    if (cost > 500) return 'text-yellow-400';
    if (isProjected) return 'text-blue-400';
    return 'text-green-400';
  };

  const getCostIcon = (cost: number) => {
    if (cost === 0) return <CheckCircle className="w-4 h-4" />;
    if (cost > 1000) return <AlertTriangle className="w-4 h-4" />;
    return <DollarSign className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-6 h-6 text-violet-400 animate-spin" />
            <span className="text-white">Loading cash flow integration...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-white text-lg font-semibold mb-2">Unable to Load Data</h3>
          <p className="text-gray-400 mb-4">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-violet-600/20 rounded-lg">
              <BarChart3 className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Maintenance Cash Flow</h2>
              <p className="text-gray-400 text-sm">Vehicle maintenance integrated with your budget</p>
            </div>
          </div>

          {/* View Controls */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value as any)}
                className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1.5 text-white text-sm focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              >
                <option value="chart">Chart View</option>
                <option value="list">List View</option>
              </select>
            </div>
            <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
              <Download className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-5 h-5 text-violet-400" />
              <span className="text-white font-semibold">Total Projected</span>
            </div>
            <div className="text-2xl font-bold text-violet-400">${totalProjectedCost.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">Next 7 months</div>
          </div>

          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              <span className="text-white font-semibold">Average Monthly</span>
            </div>
            <div className="text-2xl font-bold text-green-400">${averageMonthlyCost.toFixed(0)}</div>
            <div className="text-gray-400 text-sm">Expected cost</div>
          </div>

          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="text-white font-semibold">Highest Month</span>
            </div>
            <div className="text-2xl font-bold text-red-400">${highestMonth.totalCost.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">{formatMonth(highestMonth.month)}</div>
          </div>

          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Car className="w-5 h-5 text-blue-400" />
              <span className="text-white font-semibold">Services Planned</span>
            </div>
            <div className="text-2xl font-bold text-blue-400">
              {monthlyCosts.reduce((sum, month) => sum + month.services.length, 0)}
            </div>
            <div className="text-gray-400 text-sm">Total services</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {viewMode === 'chart' ? (
          <div className="space-y-6">
            {/* Monthly Cost Chart */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Monthly Maintenance Costs</h3>
              <div className="space-y-3">
                {monthlyCosts.map((month) => (
                  <div
                    key={month.month}
                    className={`bg-slate-700/30 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:bg-slate-700/50 ${
                      selectedMonth === month.month ? 'ring-2 ring-violet-400/50' : ''
                    }`}
                    onClick={() => {
                      setSelectedMonth(selectedMonth === month.month ? null : month.month);
                      onViewDetails?.(month.month);
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="text-white font-semibold">{formatMonth(month.month)}</div>
                        {month.isProjected && (
                          <div className="px-2 py-1 bg-blue-400/10 text-blue-400 text-xs rounded-full border border-blue-400/20">
                            Projected
                          </div>
                        )}
                      </div>
                      <div className={`flex items-center space-x-2 ${getCostColor(month.totalCost, month.isProjected)}`}>
                        {getCostIcon(month.totalCost)}
                        <span className="text-xl font-bold">${month.totalCost.toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Cost Breakdown */}
                    {month.totalCost > 0 && (
                      <div className="flex items-center space-x-4 text-sm">
                        {month.routineCost > 0 && (
                          <div className="flex items-center space-x-1 text-green-400">
                            <CheckCircle className="w-4 h-4" />
                            <span>Routine: ${month.routineCost.toFixed(2)}</span>
                          </div>
                        )}
                        {month.majorRepairCost > 0 && (
                          <div className="flex items-center space-x-1 text-red-400">
                            <AlertTriangle className="w-4 h-4" />
                            <span>Major: ${month.majorRepairCost.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Services List */}
                    {month.services.length > 0 && (
                      <div className="mt-3">
                        <div className="flex flex-wrap gap-2">
                          {month.services.map((service, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-slate-600/50 text-gray-300 text-xs rounded-full"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Progress Bar */}
                    <div className="mt-3">
                      <div className="w-full bg-slate-600 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            month.totalCost > 1000 
                              ? 'bg-gradient-to-r from-red-400 to-red-500'
                              : month.totalCost > 500
                              ? 'bg-gradient-to-r from-yellow-400 to-yellow-500'
                              : 'bg-gradient-to-r from-green-400 to-green-500'
                          }`}
                          style={{ 
                            width: `${Math.min((month.totalCost / 4000) * 100, 100)}%` 
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {monthlyCosts.map((month) => (
              <div
                key={month.month}
                className="bg-slate-700/30 rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-gray-400" />
                    <span className="text-white font-semibold">{formatMonth(month.month)}</span>
                    {month.isProjected && (
                      <div className="px-2 py-1 bg-blue-400/10 text-blue-400 text-xs rounded-full border border-blue-400/20">
                        Projected
                      </div>
                    )}
                  </div>
                  <div className={`text-xl font-bold ${getCostColor(month.totalCost, month.isProjected)}`}>
                    ${month.totalCost.toLocaleString()}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400 mb-1">Routine Maintenance</div>
                    <div className="text-green-400 font-semibold">${month.routineCost.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 mb-1">Major Repairs</div>
                    <div className="text-red-400 font-semibold">${month.majorRepairCost.toFixed(2)}</div>
                  </div>
                </div>

                {month.services.length > 0 && (
                  <div className="mt-3">
                    <div className="text-gray-400 text-sm mb-2">Services:</div>
                    <div className="flex flex-wrap gap-2">
                      {month.services.map((service, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-slate-600/50 text-gray-300 text-xs rounded-full"
                        >
                          {service}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Integration Note */}
        <div className="mt-8 p-4 bg-violet-400/10 border border-violet-400/20 rounded-xl">
          <div className="flex items-start space-x-3">
            <BarChart3 className="w-5 h-5 text-violet-400 mt-0.5" />
            <div>
              <h4 className="text-violet-400 font-semibold mb-2">Cash Flow Integration</h4>
              <p className="text-gray-300 text-sm">
                These maintenance costs are automatically integrated with your overall cash flow forecast. 
                You can view the complete financial impact in your main dashboard.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceCashFlowIntegration;
