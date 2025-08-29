import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext';
import { ArticleLibraryProvider } from './contexts/ArticleLibraryContext';

// Existing Mingus components
import Dashboard from './pages/Dashboard';
import BudgetForecast from './pages/BudgetForecast';
import HealthCheckin from './pages/HealthCheckin';
import Profile from './pages/Profile';

// Article Library components and routes
import ArticleLibraryRoutes from './routes/articleLibraryRoutes';

// Assessment components and routes
import AssessmentRoutes from './routes/assessmentRoutes';

// Layout components
import MainLayout from './components/Layout/MainLayout';
import Navigation from './components/Layout/Navigation';

// Error boundary and loading components
import ErrorBoundary from './components/shared/ErrorBoundary';
import LoadingSpinner from './components/shared/LoadingSpinner';

function App() {
    return (
        <ErrorBoundary>
            <Router>
                <AuthProvider>
                    <UserProvider>
                        <ArticleLibraryProvider>
                            <MainLayout>
                                <Navigation />
                                <Routes>
                                    {/* Existing Mingus routes */}
                                    <Route path="/" element={<Dashboard />} />
                                    <Route path="/budget" element={<BudgetForecast />} />
                                    <Route path="/health" element={<HealthCheckin />} />
                                    <Route path="/profile" element={<Profile />} />
                                    
                                    {/* Article Library routes - nested under /articles */}
                                    <Route path="/articles/*" element={<ArticleLibraryRoutes />} />
                                    
                                    {/* Assessment routes - nested under /assessments */}
                                    <Route path="/assessments/*" element={<AssessmentRoutes />} />
                                    
                                    {/* Fallback */}
                                    <Route 
                                        path="*" 
                                        element={
                                            <div className="flex items-center justify-center min-h-screen">
                                                <div className="text-center">
                                                    <h1 className="text-2xl font-bold text-gray-900 mb-4">
                                                        404 - Page Not Found
                                                    </h1>
                                                    <p className="text-gray-600 mb-4">
                                                        The page you're looking for doesn't exist.
                                                    </p>
                                                    <a 
                                                        href="/" 
                                                        className="text-blue-600 hover:text-blue-800 underline"
                                                    >
                                                        Return to Dashboard
                                                    </a>
                                                </div>
                                            </div>
                                        } 
                                    />
                                </Routes>
                            </MainLayout>
                        </ArticleLibraryProvider>
                    </UserProvider>
                </AuthProvider>
            </Router>
        </ErrorBoundary>
    );
}

export default App;
