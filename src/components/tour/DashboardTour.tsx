import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronLeft, ChevronRight, Play, SkipForward } from 'lucide-react';

interface TourStep {
  id: string;
  title: string;
  description: string;
  target: string; // CSS selector for element to highlight
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: {
    type: 'click' | 'scroll' | 'highlight';
    target?: string;
    text?: string;
  };
}

interface DashboardTourProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  onSkip: () => void;
}

const tourSteps: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Your Dashboard!',
    description: 'This is your financial wellness command center. Let\'s explore the key features that will help you achieve your goals.',
    target: '.dashboard-container',
    position: 'center'
  },
  {
    id: 'job-security',
    title: 'Job Security Score',
    description: 'Your career stability score helps you understand your professional situation and plan for the future. Higher scores mean more stability.',
    target: '#job-security-card',
    position: 'bottom',
    action: {
      type: 'highlight',
      text: 'Click to see detailed insights'
    }
  },
  {
    id: 'emergency-fund',
    title: 'Emergency Fund Tracker',
    description: 'Track your emergency savings progress. This helps you build financial security for unexpected expenses.',
    target: '#emergency-fund-card',
    position: 'bottom',
    action: {
      type: 'highlight',
      text: 'View your savings progress'
    }
  },
  {
    id: 'cash-flow',
    title: 'Cash Flow Insights',
    description: 'Monitor your income and expenses to understand your spending patterns and identify opportunities to save.',
    target: '#cash-flow-card',
    position: 'top',
    action: {
      type: 'highlight',
      text: 'Analyze your spending'
    }
  },
  {
    id: 'community',
    title: 'Community Features',
    description: 'Connect with others on similar financial journeys. Share experiences and get support from the community.',
    target: '#community-card',
    position: 'left',
    action: {
      type: 'highlight',
      text: 'Join community discussions'
    }
  },
  {
    id: 'notifications',
    title: 'Stay Updated',
    description: 'Set up notifications to get personalized insights, goal reminders, and important updates.',
    target: '.notification-settings',
    position: 'right',
    action: {
      type: 'click',
      target: '.notification-settings',
      text: 'Set up notifications'
    }
  },
  {
    id: 'accounts',
    title: 'Connect Your Accounts',
    description: 'Link your bank accounts for automatic tracking and more accurate insights.',
    target: '.account-connection',
    position: 'left',
    action: {
      type: 'click',
      target: '.account-connection',
      text: 'Connect accounts'
    }
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'You now know your way around the dashboard. Start exploring and take control of your financial wellness journey!',
    target: '.dashboard-container',
    position: 'center'
  }
];

export const DashboardTour: React.FC<DashboardTourProps> = ({
  isOpen,
  onClose,
  onComplete,
  onSkip
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isHighlighting, setIsHighlighting] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const currentTourStep = tourSteps[currentStep];

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      setTimeout(() => {
        highlightElement();
      }, 300);
    } else {
      document.body.style.overflow = 'unset';
      removeHighlight();
    }

    return () => {
      document.body.style.overflow = 'unset';
      removeHighlight();
    };
  }, [isOpen, currentStep]);

  const highlightElement = () => {
    const targetElement = document.querySelector(currentTourStep.target);
    if (targetElement) {
      setIsHighlighting(true);
      targetElement.classList.add('tour-highlight');
      positionTooltip(targetElement as HTMLElement);
    }
  };

  const removeHighlight = () => {
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight');
    });
    setIsHighlighting(false);
  };

  const positionTooltip = (targetElement: HTMLElement) => {
    if (!tooltipRef.current) return;

    const rect = targetElement.getBoundingClientRect();
    const tooltip = tooltipRef.current;
    const tooltipRect = tooltip.getBoundingClientRect();

    let top = 0;
    let left = 0;

    switch (currentTourStep.position) {
      case 'top':
        top = rect.top - tooltipRect.height - 20;
        left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        break;
      case 'bottom':
        top = rect.bottom + 20;
        left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        break;
      case 'left':
        top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
        left = rect.left - tooltipRect.width - 20;
        break;
      case 'right':
        top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
        left = rect.right + 20;
        break;
      case 'center':
        top = window.innerHeight / 2 - tooltipRect.height / 2;
        left = window.innerWidth / 2 - tooltipRect.width / 2;
        break;
    }

    tooltip.style.top = `${Math.max(20, top)}px`;
    tooltip.style.left = `${Math.max(20, Math.min(left, window.innerWidth - tooltipRect.width - 20))}px`;
  };

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleAction = () => {
    if (currentTourStep.action?.type === 'click' && currentTourStep.action.target) {
      const targetElement = document.querySelector(currentTourStep.action.target);
      if (targetElement) {
        (targetElement as HTMLElement).click();
      }
    }
    handleNext();
  };

  const handleSkip = () => {
    onSkip();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        ref={overlayRef}
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 z-60 p-2 text-white hover:text-gray-300 transition-colors"
        >
          <X size={24} />
        </button>

        {/* Tour tooltip */}
        <motion.div
          ref={tooltipRef}
          className="absolute z-60 bg-white rounded-lg shadow-2xl p-6 max-w-sm"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.3 }}
        >
          {/* Progress indicator */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex space-x-1">
              {tourSteps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === currentStep ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
            <span className="text-base leading-relaxed text-gray-500">
              {currentStep + 1} of {tourSteps.length}
            </span>
          </div>

          {/* Content */}
          <h3 className="text-lg font-semibold text-gray-900 mb-2" className="text-xl font-semibold text-gray-800 mb-3">
            {currentTourStep.title}
          </h3>
          <p className="text-gray-600 mb-4">
            {currentTourStep.description}
          </p>

          {/* Action button */}
          {currentTourStep.action && (
            <button
              onClick={handleAction}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors mb-4"
            >
              {currentTourStep.action.text}
            </button>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="flex items-center space-x-1 text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={16} />
              <span>Previous</span>
            </button>

            <div className="flex space-x-2">
              <button
                onClick={handleSkip}
                className="flex items-center space-x-1 text-gray-500 hover:text-gray-700"
              >
                <SkipForward size={16} />
                <span>Skip</span>
              </button>
              
              <button
                onClick={handleNext}
                className="flex items-center space-x-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <span>{currentStep === tourSteps.length - 1 ? 'Finish' : 'Next'}</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}; 