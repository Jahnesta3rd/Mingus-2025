import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle, 
  Wrench, 
  Car, 
  TrendingUp,
  ChevronRight,
  Filter,
  SortAsc,
  RefreshCw
} from 'lucide-react';

// Types
interface MaintenanceItem {
  id: string;
  service: string;
  description: string;
  predictedDate: string;
  estimatedCost: number;
  priority: 'routine' | 'recommended' | 'urgent';
  category: 'oil_change' | 'brake_service' | 'tire_rotation' | 'engine_service' | 'transmission' | 'other';
  confidence: number;
  mileage: number;
  isOverdue: boolean;
  lastServiceDate?: string;
  nextServiceMileage?: number;
}

interface MaintenanceForecastProps {
  vehicleId?: string;
  className?: string;
  onServiceClick?: (service: MaintenanceItem) => void;
}

const MaintenanceForecast: React.FC<MaintenanceForecastProps> = ({ 
  vehicleId, 
  className = '',
  onServiceClick 
}) => {
  const [maintenanceItems, setMaintenanceItems] = useState<MaintenanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'routine' | 'recommended' | 'urgent'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'cost' | 'priority'>('date');
  const [timeframe, setTimeframe] = useState<'3months' | '6months' | '12months'>('6months');

  // Mock data for demonstration
  const mockMaintenanceData: MaintenanceItem[] = [
    {
      id: '1',
      service: 'Oil Change',
      description: 'Regular oil change and filter replacement',
      predictedDate: '2024-02-15',
      estimatedCost: 45.99,
      priority: 'routine',
      category: 'oil_change',
      confidence: 95,
      mileage: 45000,
      isOverdue: false,
      lastServiceDate: '2023-11-15',
      nextServiceMileage: 48000
    },
    {
      id: '2',
      service: 'Brake Pad Replacement',
      description: 'Front brake pads need replacement',
      predictedDate: '2024-03-20',
      estimatedCost: 189.99,
      priority: 'urgent',
      category: 'brake_service',
      confidence: 88,
      mileage: 46000,
      isOverdue: false
    },
    {
      id: '3',
      service: 'Tire Rotation',
      description: 'Rotate tires for even wear',
      predictedDate: '2024-02-28',
      estimatedCost: 25.00,
      priority: 'routine',
      category: 'tire_rotation',
      confidence: 92,
      mileage: 45500,
      isOverdue: false,
      lastServiceDate: '2023-08-28'
    },
    {
      id: '4',
      service: 'Transmission Service',
      description: 'Transmission fluid change and inspection',
      predictedDate: '2024-04-10',
      estimatedCost: 299.99,
      priority: 'recommended',
      category: 'transmission',
      confidence: 85,
      mileage: 47000,
      isOverdue: false
    },
    {
      id: '5',
      service: 'Engine Tune-up',
      description: 'Spark plugs, air filter, and engine inspection',
      predictedDate: '2024-05-15',
      estimatedCost: 425.00,
      priority: 'recommended',
      category: 'engine_service',
      confidence: 90,
      mileage: 48000,
      isOverdue: false
    }
  ];

  useEffect(() => {
    // Simulate API call
    const fetchMaintenanceData = async () => {
      setLoading(true);
      try {
        // In a real implementation, this would call the maintenance prediction API
        await new Promise(resolve => setTimeout(resolve, 1000));
        setMaintenanceItems(mockMaintenanceData);
        setError(null);
      } catch (err) {
        setError('Failed to load maintenance data');
        console.error('Error fetching maintenance data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMaintenanceData();
  }, [vehicleId]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'recommended':
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      case 'routine':
        return 'text-green-400 bg-green-400/10 border-green-400/20';
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <AlertTriangle className="w-4 h-4" />;
      case 'recommended':
        return <Clock className="w-4 h-4" />;
      case 'routine':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Wrench className="w-4 h-4" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'oil_change':
        return <Wrench className="w-5 h-5" />;
      case 'brake_service':
        return <AlertTriangle className="w-5 h-5" />;
      case 'tire_rotation':
        return <Car className="w-5 h-5" />;
      case 'transmission':
        return <TrendingUp className="w-5 h-5" />;
      case 'engine_service':
        return <Wrench className="w-5 h-5" />;
      default:
        return <Wrench className="w-5 h-5" />;
    }
  };

  const filteredItems = maintenanceItems
    .filter(item => {
      if (filter === 'all') return true;
      return item.priority === filter;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(a.predictedDate).getTime() - new Date(b.predictedDate).getTime();
        case 'cost':
          return b.estimatedCost - a.estimatedCost;
        case 'priority':
          const priorityOrder = { urgent: 3, recommended: 2, routine: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        default:
          return 0;
      }
    });

  const totalCost = filteredItems.reduce((sum, item) => sum + item.estimatedCost, 0);
  const urgentCount = maintenanceItems.filter(item => item.priority === 'urgent').length;
  const overdueCount = maintenanceItems.filter(item => item.isOverdue).length;

  if (loading) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-6 h-6 text-violet-400 animate-spin" />
            <span className="text-white">Loading maintenance forecast...</span>
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
          <h3 className="text-white text-lg font-semibold mb-2">Unable to Load Forecast</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Try Again
          </button>
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
              <Calendar className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Maintenance Forecast</h2>
              <p className="text-gray-400 text-sm">Upcoming vehicle services</p>
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="flex items-center space-x-4">
            {urgentCount > 0 && (
              <div className="text-center">
                <div className="text-red-400 text-2xl font-bold">{urgentCount}</div>
                <div className="text-gray-400 text-xs">Urgent</div>
              </div>
            )}
            {overdueCount > 0 && (
              <div className="text-center">
                <div className="text-yellow-400 text-2xl font-bold">{overdueCount}</div>
                <div className="text-gray-400 text-xs">Overdue</div>
              </div>
            )}
            <div className="text-center">
              <div className="text-violet-400 text-2xl font-bold">${totalCost.toFixed(0)}</div>
              <div className="text-gray-400 text-xs">Total Cost</div>
            </div>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Priority Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1.5 text-white text-sm focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="all">All Services</option>
              <option value="urgent">Urgent</option>
              <option value="recommended">Recommended</option>
              <option value="routine">Routine</option>
            </select>
          </div>

          {/* Sort Options */}
          <div className="flex items-center space-x-2">
            <SortAsc className="w-4 h-4 text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1.5 text-white text-sm focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="date">Sort by Date</option>
              <option value="cost">Sort by Cost</option>
              <option value="priority">Sort by Priority</option>
            </select>
          </div>

          {/* Timeframe Filter */}
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value as any)}
              className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1.5 text-white text-sm focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="3months">Next 3 Months</option>
              <option value="6months">Next 6 Months</option>
              <option value="12months">Next 12 Months</option>
            </select>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="p-6">
        {filteredItems.length === 0 ? (
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-white text-lg font-semibold mb-2">No Services Found</h3>
            <p className="text-gray-400">No maintenance services match your current filters.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredItems.map((item, index) => (
              <div
                key={item.id}
                className={`bg-slate-700/30 backdrop-blur-sm rounded-xl border border-slate-600/30 p-4 hover:bg-slate-700/50 transition-all duration-200 cursor-pointer group ${
                  item.isOverdue ? 'ring-2 ring-red-400/50' : ''
                }`}
                onClick={() => onServiceClick?.(item)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Service Icon */}
                    <div className="p-2 bg-slate-600/50 rounded-lg">
                      {getCategoryIcon(item.category)}
                    </div>

                    {/* Service Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-white font-semibold text-lg">{item.service}</h3>
                        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(item.priority)}`}>
                          {getPriorityIcon(item.priority)}
                          <span className="capitalize">{item.priority}</span>
                        </div>
                        {item.isOverdue && (
                          <div className="flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium bg-red-400/10 text-red-400 border border-red-400/20">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Overdue</span>
                          </div>
                        )}
                      </div>

                      <p className="text-gray-300 text-sm mb-3">{item.description}</p>

                      {/* Service Metadata */}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(item.predictedDate).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-4 h-4" />
                          <span>${item.estimatedCost.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Car className="w-4 h-4" />
                          <span>{item.mileage.toLocaleString()} mi</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <TrendingUp className="w-4 h-4" />
                          <span>{item.confidence}% confidence</span>
                        </div>
                      </div>

                      {/* Progress Bar for Confidence */}
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                          <span>Prediction Confidence</span>
                          <span>{item.confidence}%</span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-1.5">
                          <div 
                            className="bg-gradient-to-r from-violet-400 to-purple-400 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${item.confidence}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Arrow */}
                  <div className="flex items-center">
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-violet-400 transition-colors" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MaintenanceForecast;
