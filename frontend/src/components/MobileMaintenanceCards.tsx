import React, { useState, useRef, useEffect } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Swipe, 
  Car, 
  DollarSign, 
  Calendar, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Wrench,
  TrendingUp,
  Star,
  Phone,
  MapPin,
  ExternalLink
} from 'lucide-react';

// Types
interface MaintenanceCard {
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
  provider?: {
    name: string;
    rating: number;
    distance: number;
    price: number;
    phone: string;
  };
}

interface MobileMaintenanceCardsProps {
  cards: MaintenanceCard[];
  className?: string;
  onCardSwipe?: (direction: 'left' | 'right', cardId: string) => void;
  onCardTap?: (card: MaintenanceCard) => void;
  onBookService?: (cardId: string) => void;
  onGetQuote?: (cardId: string) => void;
}

const MobileMaintenanceCards: React.FC<MobileMaintenanceCardsProps> = ({
  cards,
  className = '',
  onCardSwipe,
  onCardTap,
  onBookService,
  onGetQuote
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  const minSwipeDistance = 50;

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
    setIsDragging(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      onCardSwipe?.('left', cards[currentIndex].id);
    } else if (isRightSwipe && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      onCardSwipe?.('right', cards[currentIndex].id);
    }
    
    setIsDragging(false);
  };

  const handleCardTap = () => {
    if (!isDragging) {
      onCardTap?.(cards[currentIndex]);
    }
  };

  const goToNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goToPrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

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
        return <Wrench className="w-6 h-6" />;
      case 'brake_service':
        return <AlertTriangle className="w-6 h-6" />;
      case 'tire_rotation':
        return <Car className="w-6 h-6" />;
      case 'transmission':
        return <TrendingUp className="w-6 h-6" />;
      case 'engine_service':
        return <Wrench className="w-6 h-6" />;
      default:
        return <Wrench className="w-6 h-6" />;
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

  if (cards.length === 0) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-8 ${className}`}>
        <div className="text-center">
          <Car className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-white text-lg font-semibold mb-2">No Maintenance Services</h3>
          <p className="text-gray-400">No upcoming maintenance services found.</p>
        </div>
      </div>
    );
  }

  const currentCard = cards[currentIndex];

  return (
    <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header with Navigation */}
      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-violet-600/20 rounded-lg">
              <Swipe className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Maintenance Services</h2>
              <p className="text-gray-400 text-sm">Swipe to browse services</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPrevious}
              disabled={currentIndex === 0}
              className="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-white" />
            </button>
            <span className="text-gray-400 text-sm">
              {currentIndex + 1} of {cards.length}
            </span>
            <button
              onClick={goToNext}
              disabled={currentIndex === cards.length - 1}
              className="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>

        {/* Progress Dots */}
        <div className="flex justify-center space-x-2">
          {cards.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2 h-2 rounded-full transition-all duration-200 ${
                index === currentIndex 
                  ? 'bg-violet-400 w-6' 
                  : 'bg-slate-600 hover:bg-slate-500'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4">
        <div
          ref={cardRef}
          className="bg-slate-700/30 rounded-xl p-6 cursor-pointer transition-all duration-200 hover:bg-slate-700/50"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onClick={handleCardTap}
        >
          {/* Service Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-slate-600/50 rounded-xl">
                {getCategoryIcon(currentCard.category)}
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-white font-semibold text-xl">{currentCard.service}</h3>
                  <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(currentCard.priority)}`}>
                    {getPriorityIcon(currentCard.priority)}
                    <span className="capitalize">{currentCard.priority}</span>
                  </div>
                </div>
                {currentCard.isOverdue && (
                  <div className="flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium bg-red-400/10 text-red-400 border border-red-400/20 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Overdue</span>
                  </div>
                )}
                <p className="text-gray-300 text-base">{currentCard.description}</p>
              </div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-violet-400">${currentCard.estimatedCost.toFixed(0)}</div>
              <div className="text-gray-400 text-sm">Estimated Cost</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getDateColor(currentCard.predictedDate)}`}>
                {formatDate(currentCard.predictedDate)}
              </div>
              <div className="text-gray-400 text-sm">Due Date</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{currentCard.mileage.toLocaleString()}</div>
              <div className="text-gray-400 text-sm">Mileage</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{currentCard.confidence}%</div>
              <div className="text-gray-400 text-sm">Confidence</div>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
              <span>Prediction Confidence</span>
              <span>{currentCard.confidence}%</span>
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-violet-400 to-purple-400 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentCard.confidence}%` }}
              />
            </div>
          </div>

          {/* Service Provider (if available) */}
          {currentCard.provider && (
            <div className="bg-slate-600/30 rounded-xl p-4 mb-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Star className="w-4 h-4 text-yellow-400" />
                  <span className="text-white font-semibold">{currentCard.provider.name}</span>
                  <span className="text-yellow-400 text-sm">{currentCard.provider.rating}</span>
                </div>
                <div className="text-violet-400 font-semibold">${currentCard.provider.price.toFixed(2)}</div>
              </div>
              <div className="flex items-center justify-between text-sm text-gray-400">
                <div className="flex items-center space-x-1">
                  <MapPin className="w-4 h-4" />
                  <span>{currentCard.provider.distance} mi</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Phone className="w-4 h-4" />
                  <span>{currentCard.provider.phone}</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col space-y-3">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onBookService?.(currentCard.id);
              }}
              className="flex items-center justify-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              <ExternalLink className="w-5 h-5" />
              <span>Book Service</span>
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                onGetQuote?.(currentCard.id);
              }}
              className="flex items-center justify-center space-x-2 bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              <DollarSign className="w-5 h-5" />
              <span>Get Quote</span>
            </button>
          </div>
        </div>

        {/* Swipe Instructions */}
        <div className="mt-4 text-center">
          <div className="flex items-center justify-center space-x-2 text-gray-400 text-sm">
            <Swipe className="w-4 h-4" />
            <span>Swipe left or right to browse services</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileMaintenanceCards;
