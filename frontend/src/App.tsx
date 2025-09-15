import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import AssessmentModal from './components/AssessmentModal';
import MemeSplashPage from './components/MemeSplashPage';
import MoodDashboard from './components/MoodDashboard';
import MemeSettings from './components/MemeSettings';
import PageWrapper from './components/PageWrapper';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/assessment" element={
          <PageWrapper>
            <AssessmentModal />
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
        <Route path="/settings" element={
          <PageWrapper>
            <MemeSettings />
          </PageWrapper>
        } />
      </Routes>
    </Router>
  );
}

export default App;
