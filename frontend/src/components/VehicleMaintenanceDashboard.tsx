import React, { useState, useEffect } from 'react';
import { 
  Car, 
  Calendar, 
  DollarSign, 
  Shield, 
  BarChart3, 
  Smartphone,
  Desktop,
  RefreshCw,
  Settings,
  AlertTriangle,
  CheckCircle,
  TrendingUp
} from 'lucide-react';

// Import our custom components
import MaintenanceForecast from './MaintenanceForecast';
import ServiceCard from './ServiceCard';
import EmergencyFundRecommendations from './EmergencyFundRecommendations';
import MaintenanceCashFlowIntegration from './MaintenanceCashFlowIntegration';
import MobileMaintenanceCards from './MobileMaintenanceCards';

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
  provider?: {
    name: string;
    rating: number;
    distance: number;
    price: number;
    phone: string;
  };
}

interface VehicleMaintenanceDashboardProps {
  vehicleId?: string;
  className?: string;
  isMobile?: boolean;
}

const VehicleMaintenanceDashboard: React.FC<VehicleMaintenanceDashboardProps> = ({
  vehicleId,
  className = '',
  isMobile = false
}) => {
  const [maintenanceItems, setMaintenanceItems] = useState<MaintenanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'forecast' | 'services' | 'emergency' | 'cashflow'>('forecast');
  const [selectedService, setSelectedService] = useState<MaintenanceItem | null>(null);

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
      nextServiceMileage: 48000,
      provider: {
        name: 'AutoCare Plus',
        rating: 4.8,
        distance: 2.3,
        price: 43.69,
        phone: '(555) 123-4567'
      }
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
      isOverdue: false,
      provider: {
        name: 'Premium Auto Service',
        rating: 4.9,
        distance: 4.1,
        price: 227.99,
        phone: '(555) 345-6789'
      }
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
      lastServiceDate: '2023-08-28',
      provider: {
        name: 'QuickLube Express',
        rating: 4.5,
        distance: 1.8,
        price: 25.00,
        phone: '(555) 234-5678'
      }
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
      isOverdue: false,
      provider: {
        name: 'Premium Auto Service',
        rating: 4.9,
        distance: 4.1,
        price: 359.99,
        phone: '(555) 345-6789'
      }
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
      isOverdue: false,
      provider: {
        name: 'AutoCare Plus',
        rating: 4.8,
        distance: 2.3,
        price: 403.75,
        phone: '(555) 123-4567'
      }
    }
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setMaintenanceItems(mockMaintenanceData);
        setError(null);
      } catch (err) {
        setError('Failed to load maintenance data');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [vehicleId]);

  const handleServiceClick = (service: MaintenanceItem) => {
    setSelectedService(service);
    setActiveView('services');
  };

  const handleBookService = (serviceId: string, providerId?: string) => {
    console.log('Booking service:', serviceId, 'with provider:', providerId);
    // Implement booking logic
  };

  const handleGetQuote = (serviceId: string) => {
    console.log('Getting quote for service:', serviceId);
    // Implement quote logic
  };

  const handleScheduleReminder = (serviceId: string) => {
    console.log('Scheduling reminder for service:', serviceId);
    // Implement reminder logic
  };

  const handleCardSwipe = (direction: 'left' | 'right', cardId: string) => {
    console.log('Card swiped:', direction, cardId);
  };

  const handleCardTap = (card: MaintenanceItem) => {
    setSelectedService(card);
  };

  const handleSetGoal = (goal: any) => {
    console.log('Setting emergency fund goal:', goal);
    // Implement goal setting logic
  };

  const handleViewDetails = (month: string) => {
    console.log('Viewing details for month:', month);
    // Implement details view logic
  };

  const urgentCount = maintenanceItems.filter(item => item.priority === 'urgent').length;
  const overdueCount = maintenanceItems.filter(item => item.isOverdue).length;
  const totalCost = maintenanceItems.reduce((sum, item) => sum + item.estimatedCost, 0);

  if (loading) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-6 h-6 text-violet-400 animate-spin" />
            <span className="text-white">Loading maintenance dashboard...</span>
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
          <h3 className="text-white text-lg font-semibold mb-2">Unable to Load Dashboard</h3>
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
              <Car className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-white">Vehicle Maintenance</h1>
              <p className="text-gray-400 text-sm">Predictive maintenance and financial planning</p>
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveView('forecast')}
              className={`p-2 rounded-lg transition-colors ${
                activeView === 'forecast' 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
              }`}
            >
              <Calendar className="w-5 h-5" />
            </button>
            <button
              onClick={() => setActiveView('services')}
              className={`p-2 rounded-lg transition-colors ${
                activeView === 'services' 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
              }`}
            >
              <Car className="w-5 h-5" />
            </button>
            <button
              onClick={() => setActiveView('emergency')}
              className={`p-2 rounded-lg transition-colors ${
                activeView === 'emergency' 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
              }`}
            >
              <Shield className="w-5 h-5" />
            </button>
            <button
              onClick={() => setActiveView('cashflow')}
              className={`p-2 rounded-lg transition-colors ${
                activeView === 'cashflow' 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-violet-400">{maintenanceItems.length}</div>
            <div className="text-gray-400 text-sm">Services</div>
          </div>
          {urgentCount > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{urgentCount}</div>
              <div className="text-gray-400 text-sm">Urgent</div>
            </div>
          )}
          {overdueCount > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{overdueCount}</div>
              <div className="text-gray-400 text-sm">Overdue</div>
            </div>
          )}
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">${totalCost.toFixed(0)}</div>
            <div className="text-gray-400 text-sm">Total Cost</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeView === 'forecast' && (
          <div className="space-y-6">
            {isMobile ? (
              <MobileMaintenanceCards
                cards={maintenanceItems}
                onCardSwipe={handleCardSwipe}
                onCardTap={handleCardTap}
                onBookService={handleBookService}
                onGetQuote={handleGetQuote}
              />
            ) : (
              <MaintenanceForecast
                vehicleId={vehicleId}
                onServiceClick={handleServiceClick}
              />
            )}
          </div>
        )}

        {activeView === 'services' && (
          <div className="space-y-6">
            {selectedService ? (
              <ServiceCard
                service={selectedService}
                onBookService={handleBookService}
                onGetQuote={handleGetQuote}
                onScheduleReminder={handleScheduleReminder}
              />
            ) : (
              <div className="text-center py-12">
                <Car className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-white text-lg font-semibold mb-2">Select a Service</h3>
                <p className="text-gray-400">Choose a service from the forecast to view details and book.</p>
              </div>
            )}
          </div>
        )}

        {activeView === 'emergency' && (
          <EmergencyFundRecommendations
            vehicleId={vehicleId}
            onSetGoal={handleSetGoal}
          />
        )}

        {activeView === 'cashflow' && (
          <MaintenanceCashFlowIntegration
            vehicleId={vehicleId}
            onViewDetails={handleViewDetails}
          />
        )}
      </div>

      {/* Mobile Navigation */}
      {isMobile && (
        <div className="p-4 border-t border-slate-700/50 bg-slate-700/20">
          <div className="flex justify-around">
            <button
              onClick={() => setActiveView('forecast')}
              className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors ${
                activeView === 'forecast' 
                  ? 'text-violet-400' 
                  : 'text-gray-400'
              }`}
            >
              <Calendar className="w-5 h-5" />
              <span className="text-xs">Forecast</span>
            </button>
            <button
              onClick={() => setActiveView('services')}
              className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors ${
                activeView === 'services' 
                  ? 'text-violet-400' 
                  : 'text-gray-400'
              }`}
            >
              <Car className="w-5 h-5" />
              <span className="text-xs">Services</span>
            </button>
            <button
              onClick={() => setActiveView('emergency')}
              className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors ${
                activeView === 'emergency' 
                  ? 'text-violet-400' 
                  : 'text-gray-400'
              }`}
            >
              <Shield className="w-5 h-5" />
              <span className="text-xs">Emergency</span>
            </button>
            <button
              onClick={() => setActiveView('cashflow')}
              className={`flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors ${
                activeView === 'cashflow' 
                  ? 'text-violet-400' 
                  : 'text-gray-400'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              <span className="text-xs">Cash Flow</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleMaintenanceDashboard;
