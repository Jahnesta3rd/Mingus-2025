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
import ResetPasswordPage from './pages/ResetPasswordPage';
import AuthGuard from './guards/AuthGuard';
import VibeGuard from './guards/VibeGuard';
import { MCIProvider } from './context/MCIContext';
import LandingPage from './components/LandingPage';
import SignUpPage from './pages/SignUpPage';
import CheckoutPage from './pages/CheckoutPage';
import PreLaunchTracker from './pages/PreLaunchTracker';

const VibeCheckMemeWrapper: React.FC = () => {
  const navigate = useNavigate();
  return <VibeCheckMeme onContinue={() => navigate('/dashboard', { replace: true })} />;
};

const router = createBrowserRouter([
  // Public routes
  { path: '/', element: <LandingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignUpPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/forgot-password', element: <ForgotPasswordPage /> },
  { path: '/reset-password', element: <ResetPasswordPage /> },
  { path: '/checkout', element: <CheckoutPage /> },

  // Pre-launch fix tracker (internal)
  { path: '/pre-launch', element: <PreLaunchTracker /> },

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

  // Dashboard with vibe guard (layout provides global nav + user row with beta badge)
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <VibeGuard>
          <MCIProvider>
            <DashboardLayout />
          </MCIProvider>
        </VibeGuard>
      </AuthGuard>
    ),
    children: [{ index: true, element: <CareerProtectionDashboard /> }],
  },

  // Redirects
  { path: '/career-dashboard', element: <Navigate to="/dashboard" replace /> },
  { path: '*', element: <Navigate to="/" replace /> },
]);

function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
