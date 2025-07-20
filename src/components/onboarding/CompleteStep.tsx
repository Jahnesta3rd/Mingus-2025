import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingCompletion from './OnboardingCompletion';

const CompleteStep: React.FC = () => {
  const [userId, setUserId] = useState<string>('current');
  const navigate = useNavigate();

  useEffect(() => {
    // Get current user ID from auth context or localStorage
    const currentUserId = localStorage.getItem('userId') || 'current';
    setUserId(currentUserId);
  }, []);

  const handleComplete = () => {
    navigate('/dashboard');
  };

  return (
    <OnboardingCompletion 
      userId={userId}
      onComplete={handleComplete}
    />
  );
};

export default CompleteStep; 