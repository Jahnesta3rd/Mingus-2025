import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const OnboardingChoiceStep: React.FC = () => {
  const [selectedChoice, setSelectedChoice] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChoiceSelect = (choice: string) => {
    setSelectedChoice(choice);
  };

  const handleSubmit = async () => {
    if (!selectedChoice) {
      setError('Please select an option to continue');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/onboarding/choice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ choice: selectedChoice }),
      });

      if (response.ok) {
        // Navigate based on choice
        if (selectedChoice === 'deep') {
          navigate('/onboarding/profile');
        } else {
          navigate('/onboarding/financial-questionnaire');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save choice');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const choices = [
    {
      id: 'deep',
      title: 'Go Deep',
      subtitle: 'Comprehensive Setup',
      icon: '🔍',
      description: 'Complete all onboarding steps for a fully personalized experience',
      features: [
        'Detailed financial profile',
        'Comprehensive goal setting',
        'Expense tracking setup',
        'Risk tolerance assessment',
        'Lifestyle questionnaire',
        'Personalized recommendations'
      ],
      timeEstimate: '10-15 minutes',
      color: 'from-purple-500 to-indigo-600',
      hoverColor: 'from-purple-600 to-indigo-700'
    },
    {
      id: 'brief',
      title: 'Keep it Brief',
      subtitle: 'Quick Setup',
      icon: '⚡',
      description: 'Quick assessment to get you started with basic insights',
      features: [
        'Essential financial questions',
        'Basic goal identification',
        'Quick risk assessment',
        'Core recommendations',
        'Easy to upgrade later'
      ],
      timeEstimate: '3-5 minutes',
      color: 'from-green-500 to-blue-600',
      hoverColor: 'from-green-600 to-blue-700'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4" className="text-4xl font-bold text-gray-900 mb-6">
            Choose Your Onboarding Experience
          </h1>
          <p className="text-lg text-gray-600">
            Select how detailed you'd like your Mingus setup to be
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {choices.map((choice) => (
            <div
              key={choice.id}
              className={`relative bg-white rounded-2xl shadow-lg border-2 transition-all duration-300 cursor-pointer transform hover:scale-105 ${
                selectedChoice === choice.id
                  ? 'border-purple-500 shadow-xl'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleChoiceSelect(choice.id)}
            >
              {selectedChoice === choice.id && (
                <div className="absolute -top-3 -right-3 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-base leading-relaxed">✓</span>
                </div>
              )}
              
              <div className="p-8">
                <div className="text-center mb-6">
                  <div className="text-4xl mb-4">{choice.icon}</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2" className="text-2xl font-semibold text-gray-800 mb-4">{choice.title}</h2>
                  <p className="text-gray-600 mb-4">{choice.subtitle}</p>
                  <div className={`inline-block px-4 py-2 rounded-full text-base leading-relaxed font-medium text-white bg-gradient-to-r ${choice.color}`}>
                    {choice.timeEstimate}
                  </div>
                </div>

                <p className="text-gray-700 mb-6 text-center">{choice.description}</p>

                <div className="space-y-3">
                  {choice.features.map((feature, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${choice.color}`}></div>
                      <span className="text-base leading-relaxed text-gray-600">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600 text-center">{error}</p>
          </div>
        )}

        <div className="text-center">
          <button
            onClick={handleSubmit}
            disabled={!selectedChoice || isSubmitting}
            className={`px-8 py-4 text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
              selectedChoice === 'deep'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-700 hover:from-purple-700 hover:to-indigo-800'
                : selectedChoice === 'brief'
                ? 'bg-gradient-to-r from-green-600 to-blue-700 hover:from-green-700 hover:to-blue-800'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Setting up...
              </div>
            ) : (
              `Continue with ${selectedChoice === 'deep' ? 'Deep' : selectedChoice === 'brief' ? 'Brief' : ''} Setup`
            )}
          </button>
          
          <p className="text-base leading-relaxed text-gray-500 mt-4">
            You can always upgrade to the full experience later from your dashboard
          </p>
        </div>
      </div>
    </div>
  );
};

export default OnboardingChoiceStep; 