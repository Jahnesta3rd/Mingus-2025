import React from 'react';
import { Goal, Milestone } from '../../types/goals';

interface ProgressTimelineProps {
  goal: Goal;
  monthlyContribution: number;
}

const ProgressTimeline: React.FC<ProgressTimelineProps> = ({
  goal,
  monthlyContribution
}) => {
  const generateMilestones = (): Milestone[] => {
    if (!goal.targetAmount || !monthlyContribution) return [];
    
    const milestones: Milestone[] = [];
    const totalNeeded = goal.targetAmount - (goal.currentAmount || 0);
    const monthsToComplete = Math.ceil(totalNeeded / monthlyContribution);
    
    // Generate milestone points at 25%, 50%, 75%, and 100%
    const milestonePercentages = [0.25, 0.5, 0.75, 1];
    
    milestonePercentages.forEach((percentage, index) => {
      const milestoneAmount = Math.round(totalNeeded * percentage);
      const monthsFromNow = Math.ceil(milestoneAmount / monthlyContribution);
      const milestoneDate = new Date();
      milestoneDate.setMonth(milestoneDate.getMonth() + monthsFromNow);
      
      const celebration = getCelebrationMessage(percentage, goal.type);
      
      milestones.push({
        percentage,
        amount: milestoneAmount,
        date: milestoneDate,
        celebration,
        monthsFromNow
      });
    });
    
    return milestones;
  };

  const getCelebrationMessage = (percentage: number, goalType: string) => {
    if (percentage === 0.25) {
      return "🎉 First milestone reached!";
    } else if (percentage === 0.5) {
      return "🚀 Halfway there!";
    } else if (percentage === 0.75) {
      return "💪 Almost there!";
    } else {
      return "🏆 Goal achieved!";
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      year: 'numeric' 
    });
  };

  const milestones = generateMilestones();

  if (milestones.length === 0) {
    return (
      <div className="p-6 bg-gray-50 rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Your Progress Roadmap
        </h3>
        <p className="text-gray-600">
          Set your goal amount and timeline to see your progress milestones.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
      <h3 className="text-lg font-semibold text-purple-900 mb-6 flex items-center">
        <span className="text-2xl mr-2">🗺️</span>
        Your Progress Roadmap
      </h3>
      
      <div className="relative">
        {/* Progress Line */}
        <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-purple-400 to-pink-400"></div>
        
        {/* Milestones */}
        <div className="space-y-8">
          {milestones.map((milestone, index) => (
            <div key={index} className="relative flex items-start">
              {/* Milestone Point */}
              <div className="relative z-10 flex-shrink-0 w-16 h-16 bg-white border-4 border-purple-400 rounded-full flex items-center justify-center shadow-lg">
                <div className="text-xs font-bold text-purple-600">
                  {Math.round(milestone.percentage * 100)}%
                </div>
              </div>
              
              {/* Milestone Content */}
              <div className="ml-6 flex-1 bg-white p-4 rounded-xl shadow-sm border border-purple-100">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-2">
                  <div className="text-lg font-bold text-purple-900">
                    ${milestone.amount.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatDate(milestone.date)}
                  </div>
                </div>
                
                <div className="text-sm text-purple-700 mb-2">
                  {milestone.celebration}
                </div>
                
                <div className="text-xs text-gray-500">
                  {milestone.monthsFromNow} month{milestone.monthsFromNow !== 1 ? 's' : ''} from now
                </div>
                
                {/* Progress Bar */}
                <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-400 to-pink-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${milestone.percentage * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Summary */}
      <div className="mt-6 p-4 bg-white rounded-lg border border-purple-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-purple-600">
              ${monthlyContribution.toLocaleString()}
            </div>
            <div className="text-xs text-gray-600">Monthly Contribution</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">
              {Math.ceil((goal.targetAmount - (goal.currentAmount || 0)) / monthlyContribution)}
            </div>
            <div className="text-xs text-gray-600">Months to Goal</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">
              ${(goal.currentAmount || 0).toLocaleString()}
            </div>
            <div className="text-xs text-gray-600">Already Saved</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressTimeline; 