import React from 'react';
import NavigationBar from './NavigationBar';

interface PageWrapperProps {
  children: React.ReactNode;
  className?: string;
}

const PageWrapper: React.FC<PageWrapperProps> = ({ children, className = '' }) => {
  return (
    <div className={`min-h-screen bg-gray-900 text-white ${className}`}>
      {/* Skip Links for Accessibility */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:bg-violet-600 focus:text-white focus:px-4 focus:py-2 focus:rounded focus:z-50 focus:outline-none focus:ring-2 focus:ring-white"
        aria-label="Skip to main content"
      >
        Skip to main content
      </a>
      <a 
        href="#navigation" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-32 bg-violet-600 text-white px-4 py-2 rounded-lg z-50"
        aria-label="Skip to navigation menu"
      >
        Skip to navigation
      </a>
      <a 
        href="#footer" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-64 bg-violet-600 text-white px-4 py-2 rounded-lg z-50"
        aria-label="Skip to footer"
      >
        Skip to footer
      </a>
      
      {/* Header */}
      <header id="navigation" role="banner" aria-label="Site header">
        <NavigationBar />
      </header>

      {/* Main Content */}
      <main id="main-content" role="main" aria-label="Main content">
        {children}
      </main>

      {/* Footer */}
      <footer id="footer" className="bg-gray-900 border-t border-gray-800 py-12 px-4 sm:px-6 lg:px-8" role="contentinfo" aria-label="Site footer">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col items-center text-center">
            {/* Mingus Logo */}
            <div className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent mb-4">
              Mingus
            </div>
            
            {/* Copyright */}
            <p className="text-gray-400 text-sm">
              © 2024 Mingus. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PageWrapper;
