import React from 'react';
import { Goal } from '../../types/goals';

interface UserFinances {
  monthlyIncome: number;
  monthlyExpenses: number;
  currentSavings: number;
  debtPayments: number;
}

interface Adjustment {
  type: 'amount' | 'timeline';
  value: number | string;
  description: string;
}

interface FeasibilityCheckerProps {
  goal: Goal;
  userFinances: UserFinances;
  onApplyAdjustment: (adjustment: Adjustment) => void;
}

const FeasibilityChecker: React.FC<FeasibilityCheckerProps> = ({
  goal,
  userFinances,
  onApplyAdjustment
}) => {
  const analyzeFeasibility = () => {
    const monthlyContribution = goal.monthlyContribution;
    const availableIncome = userFinances.monthlyIncome - userFinances.monthlyExpenses - userFinances.debtPayments;
    const maxRecommendedContribution = userFinances.monthlyIncome * 0.3; // 30% rule
    
    const feasibilityScore = monthlyContribution / availableIncome;
    
    if (feasibilityScore <= 0.5) {
      return {
        level: 'excellent',
        icon: '🎉',
        message: 'This goal is very achievable with your current finances!',
        adjustments: []
      };
    } else if (feasibilityScore <= 0.8) {
      return {
        level: 'good',
        icon: '✅',
        message: 'This goal is achievable with some planning.',
        adjustments: [
          {
            type: 'amount' as const,
            value: Math.round(goal.targetAmount * 0.9),
            description: `Reduce target to $${Math.round(goal.targetAmount * 0.9).toLocaleString()}`
          }
        ]
      };
    } else if (feasibilityScore <= 1.2) {
      return {
        level: 'challenging',
        icon: '⚠️',
        message: 'This goal will require significant commitment and may need adjustments.',
        adjustments: [
          {
            type: 'amount' as const,
            value: Math.round(goal.targetAmount * 0.8),
            description: `Reduce target to $${Math.round(goal.targetAmount * 0.8).toLocaleString()}`
          },
          {
            type: 'timeline' as const,
            value: '2years',
            description: 'Extend timeline to 2 years'
          }
        ]
      };
    } else {
      return {
        level: 'difficult',
        icon: '🚨',
        message: 'This goal may be too ambitious with your current finances.',
        adjustments: [
          {
            type: 'amount' as const,
            value: Math.round(goal.targetAmount * 0.6),
            description: `Reduce target to $${Math.round(goal.targetAmount * 0.6).toLocaleString()}`
          },
          {
            type: 'timeline' as const,
            value: '5years',
            description: 'Extend timeline to 5+ years'
          }
        ]
      };
    }
  };

  const analysis = analyzeFeasibility();

  const getLevelStyles = (level: string) => {
    switch (level) {
      case 'excellent':
        return 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 text-green-800';
      case 'good':
        return 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200 text-blue-800';
      case 'challenging':
        return 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200 text-yellow-800';
      case 'difficult':
        return 'bg-gradient-to-r from-red-50 to-pink-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className={`p-6 rounded-xl border-2 ${getLevelStyles(analysis.level)}`}>
      <div className="flex items-start space-x-4">
        <div className="text-3xl">{analysis.icon}</div>
        <div className="flex-1">
          <h4 className="font-semibold text-lg mb-2">Goal Feasibility Analysis</h4>
          <p className="text-base leading-relaxed mb-4">{analysis.message}</p>
          
          {/* Financial Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-white/50 p-3 rounded-lg">
              <div className="text-base leading-relaxed text-gray-600 mb-1">Monthly Income</div>
              <div className="font-semibold">${userFinances.monthlyIncome.toLocaleString()}</div>
            </div>
            <div className="bg-white/50 p-3 rounded-lg">
              <div className="text-base leading-relaxed text-gray-600 mb-1">Available for Goals</div>
              <div className="font-semibold">${(userFinances.monthlyIncome - userFinances.monthlyExpenses - userFinances.debtPayments).toLocaleString()}</div>
            </div>
            <div className="bg-white/50 p-3 rounded-lg">
              <div className="text-base leading-relaxed text-gray-600 mb-1">Goal Contribution</div>
              <div className="font-semibold">${goal.monthlyContribution.toLocaleString()}</div>
            </div>
          </div>

          {/* Adjustment Suggestions */}
          {analysis.adjustments.length > 0 && (
            <div>
              <h5 className="font-medium mb-3">Consider these adjustments:</h5>
              <div className="space-y-2">
                {analysis.adjustments.map((adjustment, index) => (
                  <button
                    key={index}
                    onClick={() => onApplyAdjustment(adjustment)}
                    className="w-full text-left bg-white/70 hover:bg-white p-3 rounded-lg transition-colors border border-white/50"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-base leading-relaxed">{adjustment.description}</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeasibilityChecker; 