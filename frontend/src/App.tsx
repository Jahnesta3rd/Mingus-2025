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
import HomeScreen from './components/HomeScreen';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AuthGuard from './guards/AuthGuard';
import { TermsCheckGuard } from './components/Auth/TermsCheckGuard';
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
import OnboardingRouter from './components/OnboardingRouter';
import FinancialForecastPage from './pages/FinancialForecastPage';
import DashboardProfilePage from './pages/DashboardProfilePage';
import SnapshotPage from './pages/SnapshotPage';
import { useAuth } from './hooks/useAuth';

function localCalendarDateYmd(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const OnboardingRouteWrapper: React.FC = () => {
  const navigate = useNavigate();
  const handleOnboardingComplete = () => {
    navigate('/snapshot');
  };
  return <OnboardingRouter onComplete={handleOnboardingComplete} />;
};

const VibeCheckMemeWrapper: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const goToDashboard = () => {
    const userId = user?.id;
    if (!userId) {
      navigate('/dashboard', { replace: true });
      return;
    }
    const today = localCalendarDateYmd();
    const seenKey = `mingus_snapshot_seen_${userId}_${today}`;
    const seenToday = localStorage.getItem(seenKey) === '1';
    if (!seenToday) {
      navigate('/snapshot?returnTo=dashboard', { replace: true });
    } else {
      navigate('/dashboard', { replace: true });
    }
  };
  return <VibeCheckMeme onContinue={goToDashboard} />;
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
        <TermsCheckGuard>
          <LogoSplash />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/vibe-check-meme',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <VibeCheckMemeWrapper />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },

  // Vibe check page
  {
    path: '/vibe-check',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <VibeCheckPage />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },

  // Dashboard with vibe guard (layout provides global nav + user row with beta badge)
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <VibeGuard>
            <MCIProvider>
              <DashboardLayout />
            </MCIProvider>
          </VibeGuard>
        </TermsCheckGuard>
      </AuthGuard>
    ),
    children: [
      { index: true, element: <HomeScreen /> },
      { path: 'roster', element: <VibeTrackerPage /> },
      { path: 'forecast', element: <FinancialForecastPage /> },
      { path: 'tools', element: <CareerProtectionDashboard /> },
      { path: 'profile', element: <DashboardProfilePage /> },
      { path: 'vibe-checkups', element: <VibeCheckupsPage /> },
      { path: 'spirit', element: <SpiritFinance /> },
      { path: 'vibe-tracker', element: <Navigate to="/dashboard/roster" replace /> },
    ],
  },

  {
    path: '/onboarding',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <OnboardingRouteWrapper />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },

  {
    path: '/snapshot',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <SnapshotPage />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },

  {
    path: '/settings',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <SettingsPage />
        </TermsCheckGuard>
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
