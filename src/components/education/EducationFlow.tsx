import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, X, Settings, Type, Contrast, Volume2, VolumeX } from "lucide-react";
import EducationalCardJobSecurity from "./EducationalCardJobSecurity";
import EducationalCardCashFlow from "./EducationalCardCashFlow";
import EducationalCardWellness from "./EducationalCardWellness";
import PrivacyAssuranceCard from "./PrivacyAssuranceCard";

// Accessibility and cultural relevance features
interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  reducedMotion: boolean;
}

export default function EducationFlow({ onClose }: { onClose: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [accessibility, setAccessibility] = useState<AccessibilitySettings>({
    highContrast: false,
    largeText: false,
    screenReader: false,
    reducedMotion: false
  });

  const cards = [
    {
      title: "Career Confidence Score",
      subtitle: "Understand your professional stability",
      component: EducationalCardJobSecurity,
      icon: "💼"
    },
    {
      title: "Smart Money Moves",
      subtitle: "Plan around your real life",
      component: EducationalCardCashFlow,
      icon: "💰"
    },
    {
      title: "Whole-Life Wellness",
      subtitle: "Health and wealth connection",
      component: EducationalCardWellness,
      icon: "❤️"
    },
    {
      title: "Your Data, Your Control",
      subtitle: "Privacy and security commitment",
      component: PrivacyAssuranceCard,
      icon: "🔒"
    }
  ];

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "Escape":
        onClose();
        break;
      case "ArrowLeft":
        if (currentStep > 0) {
          setCurrentStep(currentStep - 1);
        }
        break;
      case "ArrowRight":
        if (currentStep < cards.length - 1) {
          setCurrentStep(currentStep + 1);
        }
        break;
    }
  };

  const toggleAccessibility = (setting: keyof AccessibilitySettings) => {
    setAccessibility(prev => ({
      ...prev,
      [setting]: !prev[setting]
    }));
  };

  // Apply accessibility settings
  useEffect(() => {
    const root = document.documentElement;
    
    if (accessibility.highContrast) {
      root.style.setProperty('--text-primary', '#ffffff');
      root.style.setProperty('--text-secondary', '#e5e7eb');
      root.style.setProperty('--bg-primary', '#000000');
      root.style.setProperty('--bg-secondary', '#1f2937');
    } else {
      root.style.removeProperty('--text-primary');
      root.style.removeProperty('--text-secondary');
      root.style.removeProperty('--bg-primary');
      root.style.removeProperty('--bg-secondary');
    }

    if (accessibility.largeText) {
      root.style.setProperty('--text-size', '1.2rem');
    } else {
      root.style.removeProperty('--text-size');
    }

    if (accessibility.reducedMotion) {
      root.style.setProperty('--reduced-motion', 'reduce');
    } else {
      root.style.removeProperty('--reduced-motion');
    }
  }, [accessibility]);

  const CurrentCard = cards[currentStep].component;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-labelledby="education-flow-title"
      aria-describedby="education-flow-description"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="bg-gray-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        style={{
          '--text-primary': accessibility.highContrast ? '#ffffff' : undefined,
          '--text-secondary': accessibility.highContrast ? '#e5e7eb' : undefined,
          '--bg-primary': accessibility.highContrast ? '#000000' : undefined,
          '--bg-secondary': accessibility.highContrast ? '#1f2937' : undefined,
          '--text-size': accessibility.largeText ? '1.2rem' : undefined,
        } as React.CSSProperties}
      >
        {/* Header */}
        <div className="bg-gray-800 p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800"
                aria-label="Accessibility settings"
                aria-expanded={showSettings}
                aria-controls="accessibility-panel"
              >
                <Settings className="w-5 h-5 text-gray-300" aria-hidden="true" />
              </button>
              
              <div>
                <h1 
                  id="education-flow-title" 
                  className="text-2xl font-bold text-white"
                  style={{ fontSize: accessibility.largeText ? '1.5rem' : undefined }}
                >
                  Welcome to Mingus
                </h1>
                <p 
                  id="education-flow-description"
                  className="text-gray-300 mt-1"
                  style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}
                >
                  Let's explore how we can help you build wealth, not just manage money
                </p>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="Close education flow"
            >
              <X className="w-5 h-5 text-gray-300" aria-hidden="true" />
            </button>
          </div>

          {/* Progress Indicator */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
              <span>Step {currentStep + 1} of {cards.length}</span>
              <span>{Math.round(((currentStep + 1) / cards.length) * 100)}% Complete</span>
            </div>
            <div 
              className="w-full bg-gray-700 rounded-full h-2"
              role="progressbar"
              aria-valuenow={currentStep + 1}
              aria-valuemin={1}
              aria-valuemax={cards.length}
              aria-label={`Progress: step ${currentStep + 1} of ${cards.length}`}
            >
              <motion.div
                className="bg-blue-400 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${((currentStep + 1) / cards.length) * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>

        {/* Accessibility Panel */}
        <AnimatePresence>
          {showSettings && (
            <motion.div
              id="accessibility-panel"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-gray-800 border-b border-gray-700 overflow-hidden"
              role="region"
              aria-labelledby="accessibility-title"
            >
              <div className="p-4">
                <h2 id="accessibility-title" className="text-lg font-semibold text-white mb-3">
                  Accessibility Settings
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <button
                    onClick={() => toggleAccessibility('highContrast')}
                    className={`p-3 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                      accessibility.highContrast 
                        ? 'bg-blue-600 border-blue-500 text-white' 
                        : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                    }`}
                    aria-pressed={accessibility.highContrast}
                  >
                    <Contrast className="w-5 h-5 mx-auto mb-1" aria-hidden="true" />
                    <span className="text-sm">High Contrast</span>
                  </button>
                  
                  <button
                    onClick={() => toggleAccessibility('largeText')}
                    className={`p-3 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                      accessibility.largeText 
                        ? 'bg-blue-600 border-blue-500 text-white' 
                        : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                    }`}
                    aria-pressed={accessibility.largeText}
                  >
                    <Type className="w-5 h-5 mx-auto mb-1" aria-hidden="true" />
                    <span className="text-sm">Large Text</span>
                  </button>
                  
                  <button
                    onClick={() => toggleAccessibility('screenReader')}
                    className={`p-3 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                      accessibility.screenReader 
                        ? 'bg-blue-600 border-blue-500 text-white' 
                        : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                    }`}
                    aria-pressed={accessibility.screenReader}
                  >
                    {accessibility.screenReader ? (
                      <VolumeX className="w-5 h-5 mx-auto mb-1" aria-hidden="true" />
                    ) : (
                      <Volume2 className="w-5 h-5 mx-auto mb-1" aria-hidden="true" />
                    )}
                    <span className="text-sm">Screen Reader</span>
                  </button>
                  
                  <button
                    onClick={() => toggleAccessibility('reducedMotion')}
                    className={`p-3 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                      accessibility.reducedMotion 
                        ? 'bg-blue-600 border-blue-500 text-white' 
                        : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                    }`}
                    aria-pressed={accessibility.reducedMotion}
                  >
                    <div className="w-5 h-5 mx-auto mb-1 flex items-center justify-center" aria-hidden="true">
                      <div className="w-3 h-3 border-2 border-current rounded-full"></div>
                    </div>
                    <span className="text-sm">Reduced Motion</span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2" role="img" aria-label={cards[currentStep].title}>
              {cards[currentStep].icon}
            </div>
            <h2 
              className="text-xl font-semibold text-white mb-1"
              style={{ fontSize: accessibility.largeText ? '1.3rem' : undefined }}
            >
              {cards[currentStep].title}
            </h2>
            <p 
              className="text-gray-300"
              style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}
            >
              {cards[currentStep].subtitle}
            </p>
          </div>

          <CurrentCard 
            testimonialIndex={currentStep}
            onSeeScore={() => console.log("See score clicked")}
            onSeePlanner={() => console.log("See planner clicked")}
            onSeeWellness={() => console.log("See wellness clicked")}
            onSeePrivacy={() => console.log("See privacy clicked")}
          />
        </div>

        {/* Navigation */}
        <div className="bg-gray-800 p-6 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
              className="flex items-center px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="Previous step"
            >
              <ChevronLeft className="w-4 h-4 mr-1" aria-hidden="true" />
              Previous
            </button>

            <div className="flex space-x-2">
              {cards.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-3 h-3 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                    index === currentStep ? 'bg-blue-400' : 'bg-gray-600 hover:bg-gray-500'
                  }`}
                  aria-label={`Go to step ${index + 1}`}
                  aria-current={index === currentStep ? 'step' : undefined}
                />
              ))}
            </div>

            <button
              onClick={() => setCurrentStep(Math.min(cards.length - 1, currentStep + 1))}
              disabled={currentStep === cards.length - 1}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="Next step"
            >
              {currentStep === cards.length - 1 ? 'Finish' : 'Next'}
              <ChevronRight className="w-4 h-4 ml-1" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Footer CTA */}
        {currentStep === cards.length - 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-blue-600 p-4 text-center"
          >
            <p className="text-white font-semibold mb-2">
              Ready to take control of your financial future?
            </p>
            <button
              onClick={onClose}
              className="bg-white text-blue-600 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600"
            >
              Get Started with Mingus
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
} 