import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoadingSpinner from '../components/common/LoadingSpinner';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  // Initialize from localStorage so we don't flash spinner when token was just set (e.g. after login)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(() =>
    typeof window !== 'undefined' && localStorage.getItem('auth_token') ? true : null
  );

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      sessionStorage.setItem('redirect_after_login', location.pathname);
      navigate('/login', { replace: true });
      return;
    }
    setIsAuthenticated(true);
  }, [navigate, location.pathname]);

  if (isAuthenticated === null) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }

  return <>{children}</>;
};

export default AuthGuard;
