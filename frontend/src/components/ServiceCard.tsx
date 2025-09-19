import React, { useState } from 'react';
import { 
  DollarSign, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  Wrench, 
  Car, 
  TrendingUp,
  ChevronDown,
  ChevronUp,
  MapPin,
  Phone,
  ExternalLink,
  Star,
  Shield,
  Zap
} from 'lucide-react';

// Types
interface ServiceProvider {
  id: string;
  name: string;
  rating: number;
  distance: number;
  price: number;
  phone: string;
  address: string;
  isRecommended: boolean;
  specialties: string[];
}

interface ServiceCardProps {
  service: {
    id: string;
    service: string;
    description: string;
    predictedDate: string;
    estimatedCost: number;
    priority: 'routine' | 'recommended' | 'urgent';
    category: string;
    confidence: number;
    mileage: number;
    isOverdue: boolean;
    lastServiceDate?: string;
    nextServiceMileage?: number;
  };
  className?: string;
  onBookService?: (serviceId: string, providerId: string) => void;
  onGetQuote?: (serviceId: string) => void;
  onScheduleReminder?: (serviceId: string) => void;
}

const ServiceCard: React.FC<ServiceCardProps> = ({
  service,
  className = '',
  onBookService,
  onGetQuote,
  onScheduleReminder
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  // Mock service providers data
  const serviceProviders: ServiceProvider[] = [
    {
      id: '1',
      name: 'AutoCare Plus',
      rating: 4.8,
      distance: 2.3,
      price: service.estimatedCost * 0.95,
      phone: '(555) 123-4567',
      address: '123 Main St, City, State',
      isRecommended: true,
      specialties: ['Oil Changes', 'Brake Service', 'Engine Repair']
    },
    {
      id: '2',
      name: 'QuickLube Express',
      rating: 4.5,
      distance: 1.8,
      price: service.estimatedCost * 1.1,
      phone: '(555) 234-5678',
      address: '456 Oak Ave, City, State',
      isRecommended: false,
      specialties: ['Oil Changes', 'Tire Rotation']
    },
    {
      id: '3',
      name: 'Premium Auto Service',
      rating: 4.9,
      distance: 4.1,
      price: service.estimatedCost * 1.2,
      phone: '(555) 345-6789',
      address: '789 Pine St, City, State',
      isRecommended: true,
      specialties: ['Transmission', 'Engine Service', 'Brake Service']
    }
  ];

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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return `Overdue by ${Math.abs(diffDays)} days`;
    } else if (diffDays === 0) {
      return 'Due today';
    } else if (diffDays === 1) {
      return 'Due tomorrow';
    } else if (diffDays <= 7) {
      return `Due in ${diffDays} days`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getDateColor = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'text-red-400';
    if (diffDays <= 3) return 'text-yellow-400';
    if (diffDays <= 7) return 'text-orange-400';
    return 'text-green-400';
  };

  return (
    <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Main Card Content */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-4">
            {/* Service Icon */}
            <div className="p-3 bg-slate-600/50 rounded-xl">
              {getCategoryIcon(service.category)}
            </div>

            {/* Service Info */}
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-white font-semibold text-xl">{service.service}</h3>
                <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(service.priority)}`}>
                  {getPriorityIcon(service.priority)}
                  <span className="capitalize">{service.priority}</span>
                </div>
                {service.isOverdue && (
                  <div className="flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium bg-red-400/10 text-red-400 border border-red-400/20">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Overdue</span>
                  </div>
                )}
              </div>

              <p className="text-gray-300 text-base mb-4">{service.description}</p>

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-violet-400">${service.estimatedCost.toFixed(0)}</div>
                  <div className="text-gray-400 text-sm">Estimated Cost</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getDateColor(service.predictedDate)}`}>
                    {formatDate(service.predictedDate)}
                  </div>
                  <div className="text-gray-400 text-sm">Due Date</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{service.mileage.toLocaleString()}</div>
                  <div className="text-gray-400 text-sm">Mileage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{service.confidence}%</div>
                  <div className="text-gray-400 text-sm">Confidence</div>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                  <span>Prediction Confidence</span>
                  <span>{service.confidence}%</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-violet-400 to-purple-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${service.confidence}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Expand/Collapse Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => onGetQuote?.(service.id)}
            className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <DollarSign className="w-4 h-4" />
            <span>Get Quote</span>
          </button>
          <button
            onClick={() => onScheduleReminder?.(service.id)}
            className="flex items-center space-x-2 bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Clock className="w-4 h-4" />
            <span>Set Reminder</span>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <span>Find Providers</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Content - Service Providers */}
      {isExpanded && (
        <div className="border-t border-slate-700/50 bg-slate-700/20">
          <div className="p-6">
            <h4 className="text-white font-semibold text-lg mb-4">Recommended Service Providers</h4>
            
            <div className="space-y-4">
              {serviceProviders.map((provider) => (
                <div
                  key={provider.id}
                  className={`bg-slate-600/30 rounded-xl p-4 border transition-all duration-200 ${
                    selectedProvider === provider.id 
                      ? 'border-violet-400/50 bg-violet-400/10' 
                      : 'border-slate-600/30 hover:border-slate-500/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h5 className="text-white font-semibold">{provider.name}</h5>
                        {provider.isRecommended && (
                          <div className="flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium bg-violet-400/10 text-violet-400 border border-violet-400/20">
                            <Star className="w-3 h-3" />
                            <span>Recommended</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400 mb-3">
                        <div className="flex items-center space-x-1">
                          <Star className="w-4 h-4 text-yellow-400" />
                          <span>{provider.rating}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-4 h-4" />
                          <span>{provider.distance} mi</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-4 h-4" />
                          <span>${provider.price.toFixed(2)}</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-3">
                        {provider.specialties.map((specialty) => (
                          <span
                            key={specialty}
                            className="px-2 py-1 bg-slate-500/30 text-gray-300 text-xs rounded-full"
                          >
                            {specialty}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <div className="flex items-center space-x-1">
                          <Phone className="w-4 h-4" />
                          <span>{provider.phone}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-4 h-4" />
                          <span>{provider.address}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2 ml-4">
                      <button
                        onClick={() => setSelectedProvider(provider.id)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          selectedProvider === provider.id
                            ? 'bg-violet-600 text-white'
                            : 'bg-slate-600 hover:bg-slate-500 text-white'
                        }`}
                      >
                        Select
                      </button>
                      <button
                        onClick={() => onBookService?.(service.id, provider.id)}
                        className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        <span>Book Now</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {selectedProvider && (
              <div className="mt-6 p-4 bg-violet-400/10 border border-violet-400/20 rounded-xl">
                <div className="flex items-center space-x-2 mb-2">
                  <Shield className="w-5 h-5 text-violet-400" />
                  <span className="text-violet-400 font-semibold">Selected Provider</span>
                </div>
                <p className="text-gray-300 text-sm">
                  You've selected a service provider. Click "Book Now" to schedule your service or contact them directly.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceCard;
