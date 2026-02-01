import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoadingSpinner from '../components/common/LoadingSpinner';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token');

      if (!token) {
        sessionStorage.setItem('redirect_after_login', location.pathname);
        navigate('/login', { replace: true });
        return;
      }

      setIsAuthenticated(true);
    };

    checkAuth();
  }, [navigate, location.pathname]);

  if (isAuthenticated === null) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }

  return <>{children}</>;
};

export default AuthGuard;
