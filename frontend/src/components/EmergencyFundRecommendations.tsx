import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  DollarSign, 
  TrendingUp, 
  Target, 
  CheckCircle, 
  Clock, 
  Zap,
  PiggyBank,
  BarChart3,
  Calendar,
  ArrowRight,
  Info,
  Star
} from 'lucide-react';

// Types
interface MajorRepair {
  id: string;
  service: string;
  description: string;
  estimatedCost: number;
  predictedDate: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  category: 'engine' | 'transmission' | 'brake_system' | 'suspension' | 'electrical' | 'other';
}

interface EmergencyFundRecommendation {
  currentFund: number;
  recommendedFund: number;
  shortfall: number;
  monthlyContribution: number;
  monthsToTarget: number;
  riskLevel: 'low' | 'medium' | 'high';
  priorityActions: string[];
}

interface EmergencyFundRecommendationsProps {
  vehicleId?: string;
  className?: string;
  onSetGoal?: (goal: EmergencyFundRecommendation) => void;
}

const EmergencyFundRecommendations: React.FC<EmergencyFundRecommendationsProps> = ({
  vehicleId,
  className = '',
  onSetGoal
}) => {
  const [recommendation, setRecommendation] = useState<EmergencyFundRecommendation | null>(null);
  const [majorRepairs, setMajorRepairs] = useState<MajorRepair[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for demonstration
  const mockMajorRepairs: MajorRepair[] = [
    {
      id: '1',
      service: 'Transmission Replacement',
      description: 'Complete transmission rebuild or replacement',
      estimatedCost: 3500,
      predictedDate: '2024-08-15',
      confidence: 75,
      impact: 'high',
      category: 'transmission'
    },
    {
      id: '2',
      service: 'Engine Overhaul',
      description: 'Major engine repair or replacement',
      estimatedCost: 4500,
      predictedDate: '2024-12-20',
      confidence: 60,
      impact: 'high',
      category: 'engine'
    },
    {
      id: '3',
      service: 'Brake System Replacement',
      description: 'Complete brake system overhaul',
      estimatedCost: 1200,
      predictedDate: '2024-06-10',
      confidence: 85,
      impact: 'medium',
      category: 'brake_system'
    }
  ];

  const mockRecommendation: EmergencyFundRecommendation = {
    currentFund: 2500,
    recommendedFund: 8000,
    shortfall: 5500,
    monthlyContribution: 500,
    monthsToTarget: 11,
    riskLevel: 'medium',
    priorityActions: [
      'Increase monthly savings by $200',
      'Set up automatic transfers to emergency fund',
      'Consider a high-yield savings account',
      'Review and reduce non-essential expenses'
    ]
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setMajorRepairs(mockMajorRepairs);
        setRecommendation(mockRecommendation);
        setError(null);
      } catch (err) {
        setError('Failed to load emergency fund recommendations');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [vehicleId]);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'medium':
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      case 'low':
        return 'text-green-400 bg-green-400/10 border-green-400/20';
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return 'text-red-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'engine':
        return <Zap className="w-5 h-5" />;
      case 'transmission':
        return <TrendingUp className="w-5 h-5" />;
      case 'brake_system':
        return <AlertTriangle className="w-5 h-5" />;
      case 'suspension':
        return <BarChart3 className="w-5 h-5" />;
      case 'electrical':
        return <Zap className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const totalMajorRepairCost = majorRepairs.reduce((sum, repair) => sum + repair.estimatedCost, 0);
  const averageRepairCost = majorRepairs.length > 0 ? totalMajorRepairCost / majorRepairs.length : 0;

  if (loading) {
    return (
      <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-400"></div>
            <span className="text-white">Loading emergency fund recommendations...</span>
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
          <h3 className="text-white text-lg font-semibold mb-2">Unable to Load Recommendations</h3>
          <p className="text-gray-400 mb-4">{error}</p>
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return null;
  }

  return (
    <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-slate-700/50">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-violet-600/20 rounded-lg">
            <Shield className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Emergency Fund Recommendations</h2>
            <p className="text-gray-400 text-sm">Protect yourself from unexpected major repairs</p>
          </div>
        </div>

        {/* Risk Level Indicator */}
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 px-3 py-2 rounded-full border ${getImpactColor(recommendation.riskLevel)}`}>
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium capitalize">{recommendation.riskLevel} Risk</span>
          </div>
          <div className="text-sm text-gray-400">
            Based on {majorRepairs.length} potential major repairs
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Current vs Recommended Fund */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <PiggyBank className="w-5 h-5 text-blue-400" />
              <span className="text-white font-semibold">Current Fund</span>
            </div>
            <div className="text-3xl font-bold text-blue-400">${recommendation.currentFund.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">Available now</div>
          </div>

          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="w-5 h-5 text-violet-400" />
              <span className="text-white font-semibold">Recommended Fund</span>
            </div>
            <div className="text-3xl font-bold text-violet-400">${recommendation.recommendedFund.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">Target amount</div>
          </div>

          <div className="bg-slate-700/30 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              <span className="text-white font-semibold">Monthly Goal</span>
            </div>
            <div className="text-3xl font-bold text-green-400">${recommendation.monthlyContribution.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">To reach target in {recommendation.monthsToTarget} months</div>
          </div>
        </div>

        {/* Progress Visualization */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Fund Progress</h3>
            <span className="text-gray-400 text-sm">
              {Math.round((recommendation.currentFund / recommendation.recommendedFund) * 100)}% Complete
            </span>
          </div>
          
          <div className="w-full bg-slate-600 rounded-full h-3 mb-2">
            <div 
              className="bg-gradient-to-r from-violet-400 to-purple-400 h-3 rounded-full transition-all duration-500"
              style={{ width: `${Math.min((recommendation.currentFund / recommendation.recommendedFund) * 100, 100)}%` }}
            />
          </div>
          
          <div className="flex justify-between text-sm text-gray-400">
            <span>${recommendation.currentFund.toLocaleString()}</span>
            <span>${recommendation.recommendedFund.toLocaleString()}</span>
          </div>
        </div>

        {/* Major Repairs Overview */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-white mb-4">Potential Major Repairs</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {majorRepairs.map((repair) => (
              <div key={repair.id} className="bg-slate-700/30 rounded-xl p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-slate-600/50 rounded-lg">
                      {getCategoryIcon(repair.category)}
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">{repair.service}</h4>
                      <p className="text-gray-400 text-sm">{repair.description}</p>
                    </div>
                  </div>
                  <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border ${getImpactColor(repair.impact)}`}>
                    <span className="capitalize">{repair.impact}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-4 text-gray-400">
                    <div className="flex items-center space-x-1">
                      <DollarSign className="w-4 h-4" />
                      <span>${repair.estimatedCost.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(repair.predictedDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-violet-400 font-medium">
                    {repair.confidence}% confidence
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Actions */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-white mb-4">Priority Actions</h3>
          <div className="space-y-3">
            {recommendation.priorityActions.map((action, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-slate-700/20 rounded-lg">
                <div className="flex-shrink-0 w-6 h-6 bg-violet-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <p className="text-white">{action}</p>
                </div>
                <CheckCircle className="w-5 h-5 text-gray-400" />
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => onSetGoal?.(recommendation)}
            className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            <Target className="w-5 h-5" />
            <span>Set Emergency Fund Goal</span>
          </button>
          
          <button className="flex items-center space-x-2 bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
            <BarChart3 className="w-5 h-5" />
            <span>View Savings Plan</span>
          </button>
          
          <button className="flex items-center space-x-2 bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
            <Info className="w-5 h-5" />
            <span>Learn More</span>
          </button>
        </div>

        {/* Additional Insights */}
        <div className="mt-8 p-4 bg-violet-400/10 border border-violet-400/20 rounded-xl">
          <div className="flex items-start space-x-3">
            <Star className="w-5 h-5 text-violet-400 mt-0.5" />
            <div>
              <h4 className="text-violet-400 font-semibold mb-2">Smart Tip</h4>
              <p className="text-gray-300 text-sm">
                Based on your vehicle's age and mileage, we recommend maintaining an emergency fund 
                of at least ${recommendation.recommendedFund.toLocaleString()} to cover potential major repairs. 
                This amount is calculated based on the average cost of major repairs for similar vehicles.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyFundRecommendations;
