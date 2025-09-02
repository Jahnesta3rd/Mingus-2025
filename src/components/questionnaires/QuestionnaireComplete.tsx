import React from 'react';

interface QuestionnaireCompleteProps {
  responses: Record<string, any>;
}

const QuestionnaireComplete: React.FC<QuestionnaireCompleteProps> = ({ responses }) => {
  return (
    <div className="questionnaire-complete">
      <div className="success-message">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Thank You!</h2>
        <p>You've completed all questionnaires successfully.</p>
      </div>
      
      <div className="response-summary">
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Your Responses Summary</h3>
        <div className="summary-content">
          {Object.entries(responses).map(([category, data]) => (
            <div key={category} className="category-summary">
              <h4>{category.charAt(0).toUpperCase() + category.slice(1)}</h4>
              <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuestionnaireComplete; 