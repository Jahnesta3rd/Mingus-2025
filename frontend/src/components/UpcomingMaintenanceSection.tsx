import React, { useState } from 'react';
import { 
  Calendar, 
  Wrench, 
  AlertTriangle, 
  Clock, 
  DollarSign,
  ChevronRight,
  Filter,
  SortAsc,
  Car
} from 'lucide-react';
import { MaintenanceItem, MaintenancePrediction } from '../types/vehicle';

interface UpcomingMaintenanceSectionProps {
  maintenanceItems: MaintenanceItem[];
  predictions: MaintenancePrediction[];
  loading?: boolean;
}

const UpcomingMaintenanceSection: React.FC<UpcomingMaintenanceSectionProps> = ({ 
  maintenanceItems, 
  predictions, 
  loading = false 
}) => {
  const [sortBy, setSortBy] = useState<'date' | 'priority' | 'cost'>('date');
  const [filterBy, setFilterBy] = useState<'all' | 'overdue' | 'upcoming' | 'high_priority'>('all');

  if (loading) {
    return <MaintenanceSkeleton />;
  }

  const filteredItems = maintenanceItems.filter(item => {
    switch (filterBy) {
      case 'overdue':
        return item.isOverdue;
      case 'upcoming':
        return !item.isOverdue && item.status === 'scheduled';
      case 'high_priority':
        return item.priority === 'high' || item.priority === 'urgent';
      default:
        return true;
    }
  });

  const sortedItems = [...filteredItems].sort((a, b) => {
    switch (sortBy) {
      case 'date':
        return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
      case 'priority':
        const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      case 'cost':
        return b.estimatedCost - a.estimatedCost;
      default:
        return 0;
    }
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-100 border-green-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getDaysUntilDue = (dueDate: string) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const formatDueDate = (dueDate: string) => {
    const days = getDaysUntilDue(dueDate);
    if (days < 0) {
      return `${Math.abs(days)} days overdue`;
    } else if (days === 0) {
      return 'Due today';
    } else if (days === 1) {
      return 'Due tomorrow';
    } else if (days <= 7) {
      return `Due in ${days} days`;
    } else {
      return new Date(dueDate).toLocaleDateString();
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header with Filters */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900">Maintenance Schedule</h4>
        <div className="flex items-center gap-2">
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="all">All Items</option>
            <option value="overdue">Overdue</option>
            <option value="upcoming">Upcoming</option>
            <option value="high_priority">High Priority</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="date">Sort by Date</option>
            <option value="priority">Sort by Priority</option>
            <option value="cost">Sort by Cost</option>
          </select>
        </div>
      </div>

      {/* Maintenance Items */}
      <div className="space-y-3">
        {sortedItems.length === 0 ? (
          <div className="text-center py-8">
            <Wrench className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Maintenance Items</h3>
            <p className="text-gray-600 text-sm">
              {filterBy === 'all' 
                ? 'No maintenance items scheduled.' 
                : `No ${filterBy.replace('_', ' ')} items found.`
              }
            </p>
          </div>
        ) : (
          sortedItems.map((item) => (
            <MaintenanceItemCard key={item.id} item={item} />
          ))
        )}
      </div>

      {/* Predictions Section */}
      {predictions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            AI Predictions
          </h5>
          <div className="space-y-2">
            {predictions.slice(0, 3).map((prediction) => (
              <PredictionCard key={prediction.id} prediction={prediction} />
            ))}
          </div>
        </div>
      )}

      {/* View All Button */}
      {sortedItems.length > 0 && (
        <button className="w-full mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium py-2 border-t border-gray-200 flex items-center justify-center gap-2">
          View All Maintenance
          <ChevronRight className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

// Maintenance Item Card Component
const MaintenanceItemCard: React.FC<{ item: MaintenanceItem }> = ({ item }) => {
  const getDaysUntilDue = (dueDate: string) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const formatDueDate = (dueDate: string) => {
    const days = getDaysUntilDue(dueDate);
    if (days < 0) {
      return `${Math.abs(days)} days overdue`;
    } else if (days === 0) {
      return 'Due today';
    } else if (days === 1) {
      return 'Due tomorrow';
    } else if (days <= 7) {
      return `Due in ${days} days`;
    } else {
      return new Date(dueDate).toLocaleDateString();
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-100 border-green-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const days = getDaysUntilDue(item.dueDate);
  const isOverdue = days < 0;
  const isUrgent = days <= 3;

  return (
    <div className={`p-4 rounded-lg border transition-all hover:shadow-sm ${
      isOverdue ? 'bg-red-50 border-red-200' : 
      isUrgent ? 'bg-orange-50 border-orange-200' : 
      'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            isOverdue ? 'bg-red-100 text-red-600' :
            isUrgent ? 'bg-orange-100 text-orange-600' :
            'bg-blue-100 text-blue-600'
          }`}>
            <Wrench className="h-4 w-4" />
          </div>
          <div>
            <h5 className="font-medium text-gray-900 text-sm">{item.description}</h5>
            <p className="text-xs text-gray-600 capitalize">{item.type.replace('_', ' ')}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(item.priority)}`}>
            {item.priority.toUpperCase()}
          </span>
          <button className="text-blue-600 hover:text-blue-700 text-xs font-medium">
            Schedule
          </button>
        </div>
      </div>
      
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-gray-600">
            <Calendar className="h-3 w-3" />
            <span className={isOverdue ? 'text-red-600 font-medium' : ''}>
              {formatDueDate(item.dueDate)}
            </span>
          </div>
          
          <div className="flex items-center gap-1 text-gray-600">
            <DollarSign className="h-3 w-3" />
            <span>${item.estimatedCost.toLocaleString()}</span>
          </div>
          
          {item.mileageThreshold && (
            <div className="flex items-center gap-1 text-gray-600">
              <Gauge className="h-3 w-3" />
              <span>{item.mileageThreshold.toLocaleString()} mi</span>
            </div>
          )}
        </div>
        
        {isOverdue && (
          <div className="flex items-center gap-1 text-red-600">
            <AlertTriangle className="h-3 w-3" />
            <span className="text-xs font-medium">OVERDUE</span>
          </div>
        )}
      </div>
    </div>
  );
};

// Prediction Card Component
const PredictionCard: React.FC<{ prediction: MaintenancePrediction }> = ({ prediction }) => {
  return (
    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <h6 className="font-medium text-blue-900 text-sm">{prediction.maintenanceType}</h6>
        <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded-full">
          {Math.round(prediction.confidence * 100)}% confidence
        </span>
      </div>
      <div className="flex items-center justify-between text-xs text-blue-700">
        <span>Predicted: {new Date(prediction.predictedDate).toLocaleDateString()}</span>
        <span>Est. ${prediction.estimatedCost.toLocaleString()}</span>
      </div>
    </div>
  );
};

// Loading Skeleton
const MaintenanceSkeleton: React.FC = () => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="h-5 w-32 bg-gray-200 rounded animate-pulse" />
        <div className="flex gap-2">
          <div className="h-8 w-20 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-8 w-24 bg-gray-200 rounded-lg animate-pulse" />
        </div>
      </div>
      
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 bg-gray-200 rounded-lg animate-pulse" />
                <div className="space-y-1">
                  <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
              <div className="flex gap-2">
                <div className="h-5 w-16 bg-gray-200 rounded-full animate-pulse" />
                <div className="h-5 w-16 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex gap-4">
                <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
                <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
                <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="h-3 w-12 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UpcomingMaintenanceSection;
