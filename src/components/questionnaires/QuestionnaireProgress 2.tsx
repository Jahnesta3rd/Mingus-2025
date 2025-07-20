import React from 'react';

interface QuestionnaireProgressProps {
  currentStep: number;
  totalSteps: number;
}

const QuestionnaireProgress: React.FC<QuestionnaireProgressProps> = ({
  currentStep,
  totalSteps,
}) => {
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <div className="questionnaire-progress">
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="step-indicators">
        {Array.from({ length: totalSteps }).map((_, index) => (
          <div
            key={index}
            className={`step-indicator ${index <= currentStep ? 'active' : ''}`}
          >
            {index + 1}
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuestionnaireProgress; 