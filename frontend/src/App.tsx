import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import SignUpPage from './pages/SignUpPage';
import AssessmentModal from './components/AssessmentModal';
import MemeSplashPage from './components/MemeSplashPage';
import MoodDashboard from './components/MoodDashboard';
import MemeSettings from './components/MemeSettings';
import PageWrapper from './components/PageWrapper';
import RiskStatusTestPage from './pages/RiskStatusTestPage';
import RecommendationTiersTestPage from './pages/RecommendationTiersTestPage';
import CareerProtectionDashboard from './pages/CareerProtectionDashboard';
import DashboardPreview from './pages/DashboardPreview';
import ComprehensiveDashboardPreview from './pages/ComprehensiveDashboardPreview';
import LocationMapTestPage from './pages/LocationMapTestPage';
import SimpleJobMatchingPreview from './pages/SimpleJobMatchingPreview';
import ResumeUploadPage from './pages/ResumeUploadPage';
import VehicleAssessmentPage from './pages/VehicleAssessmentPage';
import DailyOutlookTestPage from './pages/DailyOutlookTestPage';
import DashboardTestSuite from './components/DashboardTestSuite';
import SimpleDashboardTest from './pages/SimpleDashboardTest';
import TestCareerDashboard from './pages/TestCareerDashboard';
import DebugDashboard from './pages/DebugDashboard';
import ComponentDiagnostic from './pages/ComponentDiagnostic';
import NotificationTestSuite from './components/NotificationTestSuite';
import NotificationDemo from './components/NotificationDemo';
import NotificationTestPage from './pages/NotificationTestPage';
import ABTestingManager from './components/ABTestingManager';
import { AuthProvider, useAuth } from './hooks/useAuth';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Login Page Component
const LoginPage: React.FC = () => {
  const { login, loading } = useAuth();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(email, password);
    } catch (err) {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-gradient-to-br from-violet-600 to-violet-700 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">M</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your career protection dashboard
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-violet-600 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
          
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link
                to="/signup"
                className="font-medium text-violet-600 hover:text-violet-500"
              >
                Sign up
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/assessment" element={
            <PageWrapper>
              <AssessmentModal isOpen={true} assessmentType="ai-risk" onClose={() => {}} onSubmit={() => {}} />
            </PageWrapper>
          } />
          <Route path="/meme" element={
            <PageWrapper>
              <MemeSplashPage onContinue={() => {}} onSkip={() => {}} />
            </PageWrapper>
          } />
          <Route path="/dashboard" element={
            <PageWrapper>
              <MoodDashboard userId="test-user" />
            </PageWrapper>
          } />
          <Route path="/career-dashboard" element={
            <ProtectedRoute>
              <CareerProtectionDashboard />
            </ProtectedRoute>
          } />
          <Route path="/dashboard-preview" element={<DashboardPreview />} />
          <Route path="/dashboard-demo" element={<ComprehensiveDashboardPreview />} />
          <Route path="/settings" element={
            <PageWrapper>
              <MemeSettings />
            </PageWrapper>
          } />
          <Route path="/risk-test" element={
            <PageWrapper>
              <RiskStatusTestPage />
            </PageWrapper>
          } />
          <Route path="/recommendations-test" element={
            <PageWrapper>
              <RecommendationTiersTestPage />
            </PageWrapper>
          } />
          <Route path="/location-map-test" element={
            <PageWrapper>
              <LocationMapTestPage />
            </PageWrapper>
          } />
          <Route path="/job-matching-preview" element={<SimpleJobMatchingPreview />} />
          <Route path="/resume-upload" element={
            <PageWrapper>
              <ResumeUploadPage />
            </PageWrapper>
          } />
          <Route path="/vehicle-assessment" element={
            <PageWrapper>
              <VehicleAssessmentPage />
            </PageWrapper>
          } />
          <Route path="/daily-outlook-test" element={
            <PageWrapper>
              <DailyOutlookTestPage />
            </PageWrapper>
          } />
          <Route path="/dashboard-test" element={
            <PageWrapper>
              <DashboardTestSuite />
            </PageWrapper>
          } />
          <Route path="/simple-test" element={
            <PageWrapper>
              <SimpleDashboardTest />
            </PageWrapper>
          } />
          <Route path="/test-dashboard" element={
            <PageWrapper>
              <TestCareerDashboard />
            </PageWrapper>
          } />
          <Route path="/debug-dashboard" element={
            <PageWrapper>
              <DebugDashboard />
            </PageWrapper>
          } />
          <Route path="/diagnostic" element={
            <PageWrapper>
              <ComponentDiagnostic />
            </PageWrapper>
          } />
          <Route path="/notification-test" element={
            <PageWrapper>
              <NotificationTestSuite />
            </PageWrapper>
          } />
          <Route path="/notification-demo" element={
            <PageWrapper>
              <NotificationDemo />
            </PageWrapper>
          } />
          <Route path="/notification-test-page" element={<NotificationTestPage />} />
          <Route path="/ab-testing" element={
            <ProtectedRoute>
              <ABTestingManager />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
