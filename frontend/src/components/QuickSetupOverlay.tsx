import React, { useState } from 'react';
import { X, DollarSign, Target } from 'lucide-react';

interface QuickSetupOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (data: { incomeRange: string; primaryGoal: string }) => void;
}

const QuickSetupOverlay: React.FC<QuickSetupOverlayProps> = ({ isOpen, onClose, onComplete }) => {
  const [incomeRange, setIncomeRange] = useState('');
  const [primaryGoal, setPrimaryGoal] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const incomeRanges = [
    { value: '30-50k', label: '$30,000 - $50,000' },
    { value: '50-75k', label: '$50,000 - $75,000' },
    { value: '75-100k', label: '$75,000 - $100,000' },
    { value: '100k+', label: '$100,000+' }
  ];

  const financialGoals = [
    { value: 'emergency-fund', label: 'Build Emergency Fund' },
    { value: 'debt-payoff', label: 'Pay Off Debt' },
    { value: 'investing', label: 'Start Investing' },
    { value: 'home-purchase', label: 'Save for Home' },
    { value: 'retirement', label: 'Plan for Retirement' }
  ];

  const handleSubmit = async () => {
    if (!incomeRange || !primaryGoal) return;
    
    setIsSubmitting(true);
    try {
      const response = await fetch('/api/profile/quick-setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ incomeRange, primaryGoal })
      });

      if (!response.ok) {
        throw new Error('Failed to save quick setup data');
      }

      onComplete({ incomeRange, primaryGoal });
    } catch (error) {
      console.error('Quick setup error:', error);
      // Still call onComplete to allow user to proceed
      onComplete({ incomeRange, primaryGoal });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-2xl max-w-md w-full p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          aria-label="Close and skip setup"
        >
          <X className="h-6 w-6" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            Quick Personalization
          </h2>
          <p className="text-gray-400 text-sm">
            Just 2 questions to personalize your experience
          </p>
        </div>

        {/* Income Range */}
        <div className="mb-6">
          <label className="flex items-center gap-2 text-white font-medium mb-3">
            <DollarSign className="h-5 w-5 text-violet-400" />
            Annual Income Range
          </label>
          <div className="grid grid-cols-2 gap-2">
            {incomeRanges.map(range => (
              <button
                key={range.value}
                type="button"
                onClick={() => setIncomeRange(range.value)}
                className={`p-3 rounded-lg border text-sm transition-all ${
                  incomeRange === range.value
                    ? 'bg-violet-600 border-violet-500 text-white'
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-violet-500'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Primary Goal */}
        <div className="mb-6">
          <label className="flex items-center gap-2 text-white font-medium mb-3">
            <Target className="h-5 w-5 text-violet-400" />
            Top Financial Priority
          </label>
          <div className="space-y-2">
            {financialGoals.map(goal => (
              <button
                key={goal.value}
                type="button"
                onClick={() => setPrimaryGoal(goal.value)}
                className={`w-full p-3 rounded-lg border text-left text-sm transition-all ${
                  primaryGoal === goal.value
                    ? 'bg-violet-600 border-violet-500 text-white'
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-violet-500'
                }`}
              >
                {goal.label}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={handleSubmit}
            disabled={!incomeRange || !primaryGoal || isSubmitting}
            className={`w-full py-3 rounded-lg font-semibold transition-all ${
              incomeRange && primaryGoal && !isSubmitting
                ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Saving...' : 'Continue to Dashboard'}
          </button>
          <button
            onClick={onClose}
            className="w-full py-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            I'll do this later
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickSetupOverlay;
