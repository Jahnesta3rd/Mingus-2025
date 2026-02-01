import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { getDailyVibe } from '../services/vibeService';

interface VibeGuardProps {
  children: React.ReactNode;
}

const VibeGuard: React.FC<VibeGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const checkVibe = async () => {
      // Skip if on vibe-check page
      if (location.pathname === '/vibe-check') {
        setChecked(true);
        return;
      }

      // Check session storage
      const today = new Date().toISOString().split('T')[0];
      const lastDate = sessionStorage.getItem('last_vibe_date');

      if (lastDate === today) {
        setChecked(true);
        return;
      }

      // Check with API
      try {
        const data = await getDailyVibe();

        if (data.has_vibe && data.vibe) {
          sessionStorage.setItem('prefetched_vibe', JSON.stringify(data.vibe));
          navigate('/vibe-check', { replace: true });
          return;
        } else {
          sessionStorage.setItem('last_vibe_date', today);
        }
      } catch (error) {
        console.error('Vibe check error:', error);
      }

      setChecked(true);
    };

    checkVibe();
  }, [navigate, location.pathname]);

  if (!checked) {
    return <LoadingSpinner fullScreen message="Loading your dashboard..." />;
  }

  return <>{children}</>;
};

export default VibeGuard;
