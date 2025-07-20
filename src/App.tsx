import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { TabNavigation } from './components/common/TabNavigation';
import { BaseCaseTab } from './components/dashboard/BaseCaseTab';
import { CareerGrowthTab } from './components/dashboard/CareerGrowthTab';
import { EmergencyExpensesTab } from './components/dashboard/EmergencyExpensesTab';
import { HealthImpactTab } from './components/dashboard/HealthImpactTab';
import { OnboardingTab } from './components/dashboard/OnboardingTab';
import { DashboardHeader } from './components/dashboard/DashboardHeader';
import { useDashboardStore } from './store/dashboardStore';

// Import onboarding step components
import WelcomeStep from './components/onboarding/WelcomeStep';
import OnboardingChoiceStep from './components/onboarding/OnboardingChoiceStep';
import ProfileStep from './components/onboarding/ProfileStep';
import PreferencesStep from './components/onboarding/PreferencesStep';
import ExpensesStep from './components/onboarding/ExpensesStep';
import CompleteStep from './components/onboarding/CompleteStep';
import FinancialQuestionnaireStep from './components/onboarding/FinancialQuestionnaireStep';
import LifestyleQuestionnaireStep from './components/onboarding/LifestyleQuestionnaireStep';
import OnboardingFlowGuard from './components/onboarding/OnboardingFlowGuard';

// Import GoalsSetup component
import GoalsSetup from './components/onboarding/GoalsSetup';

function Dashboard() {
  const activeTab = useDashboardStore((state) => state.activeTab);

  return (
    <div className="min-h-screen bg-gray-100">
      <DashboardHeader />
      <TabNavigation />
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'onboarding' && <OnboardingTab />}
        {activeTab === 'base-case' && <BaseCaseTab />}
        {activeTab === 'career-growth' && <CareerGrowthTab />}
        {activeTab === 'emergency-expenses' && <EmergencyExpensesTab />}
        {activeTab === 'health-impact' && <HealthImpactTab />}
      </main>
    </div>
  );
}

// Wrapper component for onboarding steps with flow guard
const OnboardingStepWrapper: React.FC<{ 
  stepId: string; 
  children: React.ReactNode; 
}> = ({ stepId, children }) => {
  // TODO: Get userId from auth context
  const userId = "user_123"; // This should come from your auth system
  
  return (
    <OnboardingFlowGuard stepId={stepId} userId={userId}>
      {children}
    </OnboardingFlowGuard>
  );
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Onboarding Routes with Flow Guards */}
        <Route 
          path="/onboarding/welcome" 
          element={
            <OnboardingStepWrapper stepId="welcome">
              <WelcomeStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/choice" 
          element={
            <OnboardingStepWrapper stepId="choice">
              <OnboardingChoiceStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/profile" 
          element={
            <OnboardingStepWrapper stepId="profile_setup">
              <ProfileStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/preferences" 
          element={
            <OnboardingStepWrapper stepId="preferences">
              <PreferencesStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/expenses" 
          element={
            <OnboardingStepWrapper stepId="expenses">
              <ExpensesStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/goals" 
          element={
            <OnboardingStepWrapper stepId="goals_setup">
              <GoalsSetup />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/financial-questionnaire" 
          element={
            <OnboardingStepWrapper stepId="financial_questionnaire">
              <FinancialQuestionnaireStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/lifestyle-questionnaire" 
          element={
            <OnboardingStepWrapper stepId="lifestyle_questionnaire">
              <LifestyleQuestionnaireStep />
            </OnboardingStepWrapper>
          } 
        />
        <Route 
          path="/onboarding/complete" 
          element={
            <OnboardingStepWrapper stepId="complete">
              <CompleteStep />
            </OnboardingStepWrapper>
          } 
        />
        
        {/* Dashboard Routes */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App; 