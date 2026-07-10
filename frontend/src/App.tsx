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
import PreLaunchTracker from './pages/PreLaunchTracker';
import { RedirectWithQuery } from './components/routing/RedirectWithQuery';
import AdminRoute from './components/AdminRoute';
import BetaAdminDashboard from './pages/BetaAdminDashboard';
import VibeCheckupsPage from './pages/VibeCheckupsPage';
import CheckupsHub from './components/CheckupsHub';
import { WeeklyCheckinForm } from './components/wellness/WeeklyCheckinForm';
import {
  DashBodyWellnessCheckup,
  DashHousingRoofCheckup,
  DashMindMoodCheckup,
  DashRelationshipsCheckup,
  DashSpiritCalmCheckup,
  DashVehicleHealthCheckup,
} from './components/checkups';
import BodyCheckPage from './pages/BodyCheckPage';
import RoofCheckPage from './pages/RoofCheckPage';
import VehicleCheckPage from './pages/VehicleCheckPage';
import VibeTrackerPage from './pages/VibeTrackerPage';
import SpiritFinance from './pages/SpiritFinance';
import SettingsPage from './pages/SettingsPage';
import OnboardingRouter from './components/OnboardingRouter';
import FinancialForecastPage from './pages/FinancialForecastPage';
import EnhancedCalculatorPage from './pages/EnhancedCalculatorPage';
import ScenarioManagement from './components/ScenarioManagement';
import WaterfallPage from './pages/WaterfallPage';
import UpgradePage from './pages/UpgradePage';
import DashboardProfilePage from './pages/DashboardProfilePage';
import SnapshotPage from './pages/SnapshotPage';
import HealthInsuranceAdvisor from './components/HealthInsuranceAdvisor';
import { useAuth } from './hooks/useAuth';
import { LeadGenAssessment } from './pages/LeadGenAssessment';
import { PublicAssessmentResults } from './pages/PublicAssessmentResults';
import PurchasePlanView from './components/BackToSchool/PurchasePlanView';
import BTSSetupPage from './components/BackToSchool/BTSSetupPage';
import ProductPickerUI from './components/BackToSchool/ProductPickerUI';
import CheckoutUI from './components/BackToSchool/CheckoutUI';

function localCalendarDateYmd(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const OnboardingRouteWrapper: React.FC = () => {
  const navigate = useNavigate();
  const handleOnboardingComplete = (destination?: 'dashboard' | 'goal-planning') => {
    if (destination === 'goal-planning') {
      navigate('/dashboard/tools?tab=goal-planning', { replace: true });
      return;
    }
    navigate('/snapshot', { replace: true });
  };
  return <OnboardingRouter onComplete={handleOnboardingComplete} />;
};

const VibeCheckMemeWrapper: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const goToDashboard = () => {
    void fetch('/api/profile/vibe-moment-shown', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    }).catch((err) => console.warn('vibe-moment-shown failed:', err));

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
  { path: '/signup', element: <RedirectWithQuery toPath="/register" /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/forgot-password', element: <ForgotPasswordPage /> },
  { path: '/reset-password', element: <ResetPasswordPage /> },
  { path: '/checkout', element: <Navigate to="/register" replace /> },
  { path: '/beta', element: <Navigate to="/register?beta=1" replace /> },
  { path: '/beta/welcome', element: <Navigate to="/welcome" replace /> },
  { path: '/assessments', element: <LeadGenAssessment /> },
  { path: '/assessment-results/:assessmentId', element: <PublicAssessmentResults /> },
  { path: '/enhanced-calculator', element: <EnhancedCalculatorPage /> },
  { path: '/scenarios', element: <ScenarioManagement /> },
  { path: '/vibe-checkups', element: <VibeCheckupsPage /> },
  {
    path: '/body-check',
    element: (
      <AuthGuard>
        <BodyCheckPage />
      </AuthGuard>
    ),
  },
  {
    path: '/roof-check',
    element: (
      <AuthGuard>
        <RoofCheckPage />
      </AuthGuard>
    ),
  },
  {
    path: '/vehicle-check',
    element: (
      <AuthGuard>
        <VehicleCheckPage />
      </AuthGuard>
    ),
  },

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
      { index: true, element: <Navigate to="/dashboard/tools" replace /> },
      { path: 'roster', element: <VibeTrackerPage /> },
      { path: 'forecast', element: <FinancialForecastPage /> },
      { path: 'waterfall', element: <WaterfallPage /> },
      { path: 'upgrade', element: <UpgradePage /> },
      { path: 'tools', element: <CareerProtectionDashboard /> },
      { path: 'goals', element: <Navigate to="/dashboard/tools?tab=goal-planning" replace /> },
      { path: 'profile', element: <DashboardProfilePage /> },
      { path: 'vibe-checkups', element: <CheckupsHub /> },
      { path: 'weekly-checkin', element: <WeeklyCheckinForm /> },
      { path: 'checkups/body', element: <DashBodyWellnessCheckup /> },
      { path: 'checkups/mind-mood', element: <DashMindMoodCheckup /> },
      { path: 'checkups/spirit-calm', element: <DashSpiritCalmCheckup /> },
      { path: 'checkups/housing-roof', element: <DashHousingRoofCheckup /> },
      { path: 'checkups/relationships', element: <DashRelationshipsCheckup /> },
      { path: 'checkups/vehicle', element: <DashVehicleHealthCheckup /> },
      { path: 'spirit', element: <SpiritFinance /> },
      { path: 'benefits/insurance', element: <HealthInsuranceAdvisor /> },
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

  {
    path: '/bts/setup',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <BTSSetupPage />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/bts/:sessionId/plan',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <PurchasePlanView />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/bts/:sessionId/shop/:tier',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <ProductPickerUI />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/bts/:sessionId/checkout',
    element: (
      <AuthGuard>
        <TermsCheckGuard>
          <CheckoutUI />
        </TermsCheckGuard>
      </AuthGuard>
    ),
  },

  // Redirects
  { path: '/pricing', element: <Navigate to="/" replace /> },
  { path: '/career-dashboard', element: <Navigate to="/dashboard" replace /> },
  { path: '/settings/upgrade', element: <Navigate to="/dashboard/upgrade" replace /> },
  { path: '/settings/career', element: <Navigate to="/dashboard/tools?tab=you" replace /> },
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
