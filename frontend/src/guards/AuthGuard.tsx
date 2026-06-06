import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';

interface AuthGuardProps {
  children: React.ReactNode;
}

function hasClientAuthMarker(): boolean {
  try {
    return !!(
      localStorage.getItem('auth_token') || localStorage.getItem('mingus_token')
    );
  } catch {
    return false;
  }
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  const clientAuthed = hasClientAuthMarker();
  const allowed = isAuthenticated || clientAuthed;

  useEffect(() => {
    if (loading) return;
    if (!allowed) {
      sessionStorage.setItem('redirect_after_login', location.pathname);
      navigate('/login', { replace: true });
    }
  }, [loading, allowed, navigate, location.pathname]);

  if (loading && !clientAuthed) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }

  if (!allowed) {
    return null;
  }

  return <>{children}</>;
};

export default AuthGuard;
