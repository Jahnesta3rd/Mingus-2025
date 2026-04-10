import { HelmetProvider } from 'react-helmet-async';
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
import BetaLanding from './pages/BetaLanding';
import BetaWelcome from './pages/BetaWelcome';
import AdminRoute from './components/AdminRoute';
import BetaAdminDashboard from './pages/BetaAdminDashboard';
import VibeCheckupsPage from './pages/VibeCheckupsPage';
import BodyCheckPage from './pages/BodyCheckPage';
import RoofCheckPage from './pages/RoofCheckPage';
import VehicleCheckPage from './pages/VehicleCheckPage';
import VibeTrackerPage from './pages/VibeTrackerPage';
import SpiritFinance from './pages/SpiritFinance';
import SettingsPage from './pages/SettingsPage';
import OnboardingPage from './pages/OnboardingPage';

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
  { path: '/beta', element: <BetaLanding /> },
  { path: '/beta/welcome', element: <BetaWelcome /> },
  { path: '/vibe-checkups', element: <VibeCheckupsPage /> },
  { path: '/body-check', element: <BodyCheckPage /> },
  { path: '/roof-check', element: <RoofCheckPage /> },
  { path: '/vehicle-check', element: <VehicleCheckPage /> },

  // Pre-launch fix tracker (internal)
  { path: '/pre-launch', element: <PreLaunchTracker /> },

  {
    path: '/admin/beta',
    element: (
      <AdminRoute>
        <BetaAdminDashboard />
      </AdminRoute>
    ),
  },

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
    children: [
      { index: true, element: <CareerProtectionDashboard /> },
      { path: 'vibe-tracker', element: <VibeTrackerPage /> },
      { path: 'spirit', element: <SpiritFinance /> },
    ],
  },

  {
    path: '/onboarding',
    element: (
      <AuthGuard>
        <OnboardingPage />
      </AuthGuard>
    ),
  },

  {
    path: '/settings',
    element: (
      <AuthGuard>
        <SettingsPage />
      </AuthGuard>
    ),
  },

  // Redirects
  { path: '/career-dashboard', element: <Navigate to="/dashboard" replace /> },
  { path: '*', element: <Navigate to="/" replace /> },
]);

function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
    </HelmetProvider>
  );
}

export default App;
