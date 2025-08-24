import React from 'react';

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
  progressPercentage: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentStep,
  totalSteps,
  progressPercentage
}) => {
  const steps = [
    { id: 1, name: 'Basic Info', description: 'Contact & salary details' },
    { id: 2, name: 'Detailed Profile', description: 'Career goals & skills' },
    { id: 3, name: 'Generate Report', description: 'Personalized insights' }
  ];

  return (
    <div className="mb-8">
      {/* Progress Bar */}
      <div className="relative mb-6">
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        
        {/* Step Indicators */}
        <div className="flex justify-between mt-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                  step.id <= currentStep
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step.id < currentStep ? '✓' : step.id}
              </div>
              <div className="mt-2 text-center">
                <div className={`text-xs font-medium ${
                  step.id <= currentStep ? 'text-gray-900' : 'text-gray-500'
                }`}>
                  {step.name}
                </div>
                <div className="text-xs text-gray-400 hidden sm:block">
                  {step.description}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Step Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-blue-900">
              Step {currentStep} of {totalSteps}: {steps[currentStep - 1]?.name}
            </h3>
            <p className="text-sm text-blue-700">
              {steps[currentStep - 1]?.description}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">
              {Math.round(progressPercentage)}%
            </div>
            <div className="text-sm text-blue-600">Complete</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator; 