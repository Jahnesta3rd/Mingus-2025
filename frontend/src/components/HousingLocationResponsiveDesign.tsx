import React from 'react';

/**
 * Responsive Design Guidelines for Housing Location Integration
 * 
 * This component documents the responsive design patterns used throughout
 * the housing location integration to ensure consistency with the existing
 * MINGUS design system.
 */

export const ResponsiveDesignGuidelines = () => {
  return (
    <div className="hidden">
      {/* This component is for documentation purposes only */}
      <div className="responsive-design-guidelines">
        {/* Mobile First Approach */}
        <div className="mobile-first">
          {/* Base styles for mobile (320px+) */}
          <div className="grid grid-cols-1 gap-4 p-4">
            {/* Mobile: Single column layout */}
            <div className="housing-tile-mobile">
              <div className="p-4 bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <div className="h-6 w-6 text-blue-600">🏠</div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Housing Location</h3>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600">
                      Professional
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tablet Breakpoint (768px+) */}
        <div className="tablet-breakpoint">
          <div className="md:grid md:grid-cols-2 md:gap-6 md:p-6">
            {/* Tablet: Two column layout */}
            <div className="housing-tile-tablet">
              <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <div className="h-6 w-6 text-blue-600">🏠</div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Housing Location</h3>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600">
                        Professional
                      </span>
                    </div>
                  </div>
                  <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                    Upgrade
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Desktop Breakpoint (1024px+) */}
        <div className="desktop-breakpoint">
          <div className="lg:grid lg:grid-cols-3 lg:gap-8 lg:p-8">
            {/* Desktop: Three column layout */}
            <div className="housing-tile-desktop">
              <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <div className="h-6 w-6 text-blue-600">🏠</div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Housing Location</h3>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600">
                        Professional
                      </span>
                    </div>
                  </div>
                  <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                    Upgrade
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Typography Scale */}
        <div className="typography-scale">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl lg:text-4xl">H1 - Main Headlines</h1>
          <h2 className="text-xl font-semibold text-gray-900 sm:text-2xl lg:text-3xl">H2 - Section Headers</h2>
          <h3 className="text-lg font-semibold text-gray-900 sm:text-xl lg:text-2xl">H3 - Component Titles</h3>
          <h4 className="text-base font-medium text-gray-900 sm:text-lg lg:text-xl">H4 - Subsection Headers</h4>
          <p className="text-sm text-gray-600 sm:text-base lg:text-lg">Body text with responsive sizing</p>
          <p className="text-xs text-gray-500 sm:text-sm lg:text-base">Small text and captions</p>
        </div>

        {/* Spacing System */}
        <div className="spacing-system">
          <div className="space-y-1">space-y-1 (4px)</div>
          <div className="space-y-2">space-y-2 (8px)</div>
          <div className="space-y-3">space-y-3 (12px)</div>
          <div className="space-y-4">space-y-4 (16px)</div>
          <div className="space-y-6">space-y-6 (24px)</div>
          <div className="space-y-8">space-y-8 (32px)</div>
        </div>

        {/* Color System */}
        <div className="color-system">
          <div className="bg-blue-50 text-blue-800">Primary Blue</div>
          <div className="bg-green-50 text-green-800">Success Green</div>
          <div className="bg-yellow-50 text-yellow-800">Warning Yellow</div>
          <div className="bg-red-50 text-red-800">Error Red</div>
          <div className="bg-gray-50 text-gray-800">Neutral Gray</div>
        </div>

        {/* Interactive States */}
        <div className="interactive-states">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors">
            Primary Button
          </button>
          <button className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors">
            Secondary Button
          </button>
          <button className="text-blue-600 hover:text-blue-700 font-medium transition-colors">
            Text Link
          </button>
        </div>

        {/* Form Elements */}
        <div className="form-elements">
          <input 
            type="text" 
            placeholder="Search locations..." 
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
            <option>Select option</option>
          </select>
        </div>

        {/* Loading States */}
        <div className="loading-states">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>

        {/* Error States */}
        <div className="error-states">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <div className="h-5 w-5 text-red-500">⚠️</div>
              <p className="text-sm text-red-700">Error message</p>
            </div>
          </div>
        </div>

        {/* Accessibility Features */}
        <div className="accessibility-features">
          <button 
            className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label="Accessible button"
          >
            Accessible Button
          </button>
          <div role="alert" aria-live="polite">
            Live region for dynamic content
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponsiveDesignGuidelines;
