/**
 * MINGUS Article Library - React Router Configuration
 * ==================================================
 * Route definitions and navigation setup for the article library
 */

import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ARTICLE_LIBRARY_CONFIG } from '../config/articleLibrary';
import { BookOpen, Search, Star, FolderOpen, Tag, BarChart3, Settings, FileText, UserCheck } from 'lucide-react';

// =====================================================
// LAZY LOADED COMPONENTS
// =====================================================

// Main article library components
const ArticleLibraryHome = lazy(() => import('../components/articles/ArticleLibraryHome'));
const ArticleSearch = lazy(() => import('../components/articles/ArticleSearch'));
const ArticleRecommendations = lazy(() => import('../components/articles/ArticleRecommendations'));
const ArticleFolders = lazy(() => import('../components/articles/ArticleFolders'));
const ArticleTopics = lazy(() => import('../components/articles/ArticleTopics'));
const ArticleAnalytics = lazy(() => import('../components/articles/ArticleAnalytics'));
const ArticleAssessment = lazy(() => import('../components/articles/ArticleAssessment'));
const ArticleSettings = lazy(() => import('../components/articles/ArticleSettings'));

// Article detail components
const ArticleDetail = lazy(() => import('../components/articles/ArticleDetail'));
const FolderDetail = lazy(() => import('../components/articles/FolderDetail'));
const TopicDetail = lazy(() => import('../components/articles/TopicDetail'));

// Shared components
const LoadingSpinner = lazy(() => import('../components/shared/LoadingSpinner'));
const ErrorBoundary = lazy(() => import('../components/shared/ErrorBoundary'));
const ProtectedRoute = lazy(() => import('../components/auth/ProtectedRoute'));

// =====================================================
// LOADING COMPONENTS
// =====================================================

const ArticleLibraryLoading = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
    <span className="ml-3 text-lg text-gray-600">Loading Article Library...</span>
  </div>
);

const ComponentLoading = () => (
  <div className="flex items-center justify-center p-8">
    <LoadingSpinner />
  </div>
);

// =====================================================
// FEATURE FLAG WRAPPER
// =====================================================

const FeatureFlagRoute = ({ feature, children, fallback = null }) => {
  const isEnabled = ARTICLE_LIBRARY_CONFIG.FEATURES[feature];
  
  if (!isEnabled) {
    return fallback || <Navigate to="/articles" replace />;
  }
  
  return children;
};

// =====================================================
// ROUTE COMPONENTS
// =====================================================

const ArticleLibraryRoutes = () => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<ArticleLibraryLoading />}>
        <Routes>
          {/* Main Article Library Routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <ArticleLibraryHome />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/search" 
            element={
              <ProtectedRoute>
                <ArticleSearch />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/recommendations" 
            element={
              <ProtectedRoute>
                <FeatureFlagRoute feature="AI_RECOMMENDATIONS">
                  <ArticleRecommendations />
                </FeatureFlagRoute>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/folders" 
            element={
              <ProtectedRoute>
                <FeatureFlagRoute feature="ARTICLE_FOLDERS">
                  <ArticleFolders />
                </FeatureFlagRoute>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/topics" 
            element={
              <ProtectedRoute>
                <ArticleTopics />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/analytics" 
            element={
              <ProtectedRoute>
                <FeatureFlagRoute feature="ANALYTICS">
                  <ArticleAnalytics />
                </FeatureFlagRoute>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/assessment" 
            element={
              <ProtectedRoute>
                <ArticleAssessment />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <ArticleSettings />
              </ProtectedRoute>
            } 
          />
          
          {/* Detail Routes */}
          <Route 
            path="/:id" 
            element={
              <ProtectedRoute>
                <Suspense fallback={<ComponentLoading />}>
                  <ArticleDetail />
                </Suspense>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/folders/:folderId" 
            element={
              <ProtectedRoute>
                <FeatureFlagRoute feature="ARTICLE_FOLDERS">
                  <Suspense fallback={<ComponentLoading />}>
                    <FolderDetail />
                  </Suspense>
                </FeatureFlagRoute>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/topics/:topicId" 
            element={
              <ProtectedRoute>
                <Suspense fallback={<ComponentLoading />}>
                  <TopicDetail />
                </Suspense>
              </ProtectedRoute>
            } 
          />
          
          {/* Catch-all route */}
          <Route 
            path="*" 
            element={<Navigate to="/" replace />} 
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
};

// =====================================================
// NAVIGATION CONFIGURATION
// =====================================================

export const getArticleLibraryNavigation = () => {
  return [
    {
      id: 'home',
      label: 'All Articles',
      path: '/articles',
      icon: <BookOpen className="w-4 h-4" />,
      description: 'Browse all articles',
    },
    {
      id: 'search',
      label: 'Search',
      path: '/articles/search',
      icon: <Search className="w-4 h-4" />,
      description: 'Search articles',
    },
    {
      id: 'recommendations',
      label: 'Recommendations',
      path: '/articles/recommendations',
      icon: <Star className="w-4 h-4" />,
      description: 'Personalized recommendations',
      featureFlag: 'AI_RECOMMENDATIONS',
    },
    {
      id: 'folders',
      label: 'Folders',
      path: '/articles/folders',
      icon: <FolderOpen className="w-4 h-4" />,
      description: 'Organize articles in folders',
      featureFlag: 'ARTICLE_FOLDERS',
    },
    {
      id: 'topics',
      label: 'Topics',
      path: '/articles/topics',
      icon: <Tag className="w-4 h-4" />,
      description: 'Browse by topics',
    },
    {
      id: 'analytics',
      label: 'Analytics',
      path: '/articles/analytics',
      icon: <BarChart3 className="w-4 h-4" />,
      description: 'Reading analytics and insights',
      featureFlag: 'ANALYTICS',
    },
    {
      id: 'assessment',
      label: 'Assessment',
      path: '/articles/assessment',
      icon: <UserCheck className="w-4 h-4" />,
      description: 'Take assessment tests',
    },
    {
      id: 'settings',
      label: 'Settings',
      path: '/articles/settings',
      icon: <Settings className="w-4 h-4" />,
      description: 'Article library settings',
    },
  ].filter(item => {
    // Filter by feature flags
    if (item.featureFlag) {
      return ARTICLE_LIBRARY_CONFIG.FEATURES[item.featureFlag];
    }
    return true;
  });
};

// =====================================================
// BREADCRUMB CONFIGURATION
// =====================================================

export const getBreadcrumbs = (pathname) => {
  const breadcrumbs = [
    {
      label: 'Learning Library',
      path: '/articles',
      icon: <BookOpen className="w-4 h-4" />,
    },
  ];
  
  // Add breadcrumbs based on current path
  const pathSegments = pathname.split('/').filter(Boolean);
  
  if (pathSegments.length > 1) {
    const currentSection = pathSegments[1];
    const sectionConfig = getArticleLibraryNavigation().find(
      item => item.id === currentSection
    );
    
    if (sectionConfig) {
      breadcrumbs.push({
        label: sectionConfig.label,
        path: `/articles/${currentSection}`,
        icon: sectionConfig.icon,
      });
    }
    
    // Add detail breadcrumbs
    if (pathSegments.length > 2) {
      const detailId = pathSegments[2];
      breadcrumbs.push({
        label: `ID: ${detailId}`,
        path: pathname,
        icon: <FileText className="w-4 h-4" />,
      });
    }
  }
  
  return breadcrumbs;
};

// =====================================================
// ROUTE GUARDS
// =====================================================

export const checkRouteAccess = (pathname, user) => {
  // Check if user is authenticated
  if (!user) {
    return { allowed: false, redirect: '/login' };
  }
  
  // Check feature-specific access
  const pathSegments = pathname.split('/').filter(Boolean);
  
  if (pathSegments.length > 1) {
    const section = pathSegments[1];
    
    // Check feature flags
    switch (section) {
      case 'recommendations':
        if (!ARTICLE_LIBRARY_CONFIG.FEATURES.AI_RECOMMENDATIONS) {
          return { allowed: false, redirect: '/articles' };
        }
        break;
      case 'folders':
        if (!ARTICLE_LIBRARY_CONFIG.FEATURES.ARTICLE_FOLDERS) {
          return { allowed: false, redirect: '/articles' };
        }
        break;
      case 'analytics':
        if (!ARTICLE_LIBRARY_CONFIG.FEATURES.ANALYTICS) {
          return { allowed: false, redirect: '/articles' };
        }
        break;
    }
  }
  
  return { allowed: true };
};

// =====================================================
// ROUTE METADATA
// =====================================================

export const getRouteMetadata = (pathname) => {
  const pathSegments = pathname.split('/').filter(Boolean);
  
  if (pathSegments.length === 1) {
    return {
      title: 'Learning Library - MINGUS',
      description: 'Browse and discover articles for personal development',
      keywords: 'articles, personal development, MINGUS, library',
    };
  }
  
  const section = pathSegments[1];
  const sectionConfig = getArticleLibraryNavigation().find(
    item => item.id === section
  );
  
  if (sectionConfig) {
    return {
      title: `${sectionConfig.label} - Learning Library - MINGUS`,
      description: sectionConfig.description,
      keywords: `articles, ${section.toLowerCase()}, MINGUS, library`,
    };
  }
  
  return {
    title: 'Learning Library - MINGUS',
    description: 'Browse and discover articles for personal development',
    keywords: 'articles, personal development, MINGUS, library',
  };
};

// =====================================================
// ROUTE ANIMATIONS
// =====================================================

export const getRouteAnimation = (pathname) => {
  const pathSegments = pathname.split('/').filter(Boolean);
  
  if (pathSegments.length === 1) {
    return 'fadeIn';
  }
  
  if (pathSegments.length === 2) {
    return 'slideInRight';
  }
  
  if (pathSegments.length > 2) {
    return 'slideInUp';
  }
  
  return 'fadeIn';
};

// =====================================================
// EXPORTS
// =====================================================

export default ArticleLibraryRoutes;

export {
  getArticleLibraryNavigation,
  getBreadcrumbs,
  checkRouteAccess,
  getRouteMetadata,
  getRouteAnimation,
};
