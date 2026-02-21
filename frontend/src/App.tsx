import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import LogoSplash from './components/splash/LogoSplash';
import VibeCheckPage from './components/vibe/VibeCheckPage';
import VibeCheckMeme from './components/vibe/VibeCheckMeme';
import DashboardLayout from './components/dashboard/DashboardLayout';
import MoodDashboard from './components/MoodDashboard';
import CareerProtectionDashboard from './pages/CareerProtectionDashboard';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import AuthGuard from './guards/AuthGuard';
import VibeGuard from './guards/VibeGuard';

const VibeCheckMemeWrapper: React.FC = () => {
  const navigate = useNavigate();
  return <VibeCheckMeme onContinue={() => navigate('/dashboard', { replace: true })} />;
};

const router = createBrowserRouter([
  // Public routes
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/forgot-password', element: <ForgotPasswordPage /> },

  // Logo splash (first stop after login)
  {
    path: '/welcome',
    element: (
      <AuthGuard>
        <LogoSplash />
      </AuthGuard>
    ),
  },
  {
    path: '/vibe-check-meme',
    element: (
      <AuthGuard>
        <VibeCheckMemeWrapper />
      </AuthGuard>
    ),
  },

  // Vibe check page
  {
    path: '/vibe-check',
    element: (
      <AuthGuard>
        <VibeCheckPage />
      </AuthGuard>
    ),
  },

  // Dashboard with vibe guard
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <VibeGuard>
          <CareerProtectionDashboard />
        </VibeGuard>
      </AuthGuard>
    ),
  },

  // Redirects
  { path: '/career-dashboard', element: <Navigate to="/dashboard" replace /> },
  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '*', element: <Navigate to="/dashboard" replace /> },
]);

function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
