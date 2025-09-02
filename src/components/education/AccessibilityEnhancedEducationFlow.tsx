import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Settings, 
  Type, 
  Contrast, 
  Volume2, 
  VolumeX,
  ShieldCheck,
  Calendar,
  HeartPulse,
  Lock,
  CheckCircle,
  TrendingUp,
  Building,
  Users,
  MapPin,
  DollarSign,
  AlertTriangle,
  Clock,
  Brain,
  Smile,
  EyeOff,
  UserCheck
} from "lucide-react";

// Accessibility and cultural relevance features
interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  reducedMotion: boolean;
}

// Testimonial data with diverse representation and real challenges
const testimonials = [
  { 
    quote: "Finally, a money app that gets my life - juggling student loans, childcare, and helping my parents", 
    author: "Keisha, 28, Atlanta, Healthcare Professional" 
  },
  { 
    quote: "Helped me see the connection between my stress and spending after losing my job", 
    author: "Marcus, 31, Houston, Tech Professional" 
  },
  {
    quote: "As a single mom, this helps me plan for everything - from daycare to my parents' medical bills",
    author: "Aisha, 35, Chicago, Educator"
  },
  {
    quote: "Understanding my career stability helps me plan for my family's future with confidence",
    author: "Javier, 29, Miami, Construction Manager"
  }
];

// Sample important dates for cash flow - reflecting real life challenges
const importantDates = [
  { day: 5, label: "Childcare Payment", amount: 800, type: "expense" },
  { day: 12, label: "Student Loan", amount: 350, type: "expense" },
  { day: 18, label: "Parents' Medical", amount: 200, type: "expense" },
  { day: 25, label: "Family Dinner", amount: 120, type: "expense" },
  { day: 15, label: "Payday", amount: 3200, type: "income" }
];

export default function AccessibilityEnhancedEducationFlow({ onClose }: { onClose: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
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
      icon: ShieldCheck,
      color: "text-blue-400",
      bgColor: "bg-blue-600",
      description: "We analyze your industry trends, skill demand, and local job market to give you a clear picture of your career stability. Think of it as your professional weather forecast - helping you prepare for opportunities and challenges ahead, whether you're dealing with job transitions, student loan payments, or supporting family members.",
      features: [
        "Industry growth tracking",
        "Skill gap identification", 
        "Local market insights",
        "Promotion pathway mapping"
      ],
      demoScore: 78,
      testimonialIndex: 0
    },
    {
      title: "Smart Money Moves",
      subtitle: "Plan around your real life",
      icon: Calendar,
      color: "text-green-400",
      bgColor: "bg-green-600",
      description: "We map your income and expenses against your actual life - childcare payments, student loans, family medical expenses, and community events. No more surprise broke weeks. Take control of your money to support what matters most to you and your family.",
      features: [
        "Income & expense tracking",
        "Important date planning that leaves you with the cash required on those dates",
        "Emergency buffer alerts",
        "'What-if' spending scenarios"
      ],
      demoScore: 85,
      testimonialIndex: 1
    },
    {
      title: "Whole-Life Wellness",
      subtitle: "Health and wealth connection",
      icon: HeartPulse,
      color: "text-purple-400",
      bgColor: "bg-purple-600",
      description: "Your physical and mental health directly impact your money decisions. We track how stress, relationships, and self-care connect to your spending patterns. Whether you're managing family responsibilities, work stress, or financial pressures, understanding these connections helps you build sustainable money habits.",
      features: [
        "Physical activity tracking",
        "Stress & mental health check-ins",
        "Relationship health monitoring",
        "Mindfulness practice logging"
      ],
      demoScore: 72,
      testimonialIndex: 2
    },
    {
      title: "Your Data, Your Control",
      subtitle: "Privacy and security commitment",
      icon: Lock,
      color: "text-yellow-400",
      bgColor: "bg-yellow-600",
      description: "Built for our community, by our community. Your financial and personal information stays private and secure. We understand the importance of trust when it comes to your money and your family's financial future. Your privacy isn't negotiable - it's a promise we keep.",
      features: [
        "Bank-level encryption",
        "No data selling, ever",
        "Anonymous community insights",
        "Full control over what you share"
      ],
      demoScore: 95,
      testimonialIndex: 3
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
      case "Enter":
      case " ":
        if (event.target === event.currentTarget) {
          event.preventDefault();
          setExpanded(!expanded);
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

  const handleTryIt = () => {
    setShowSuccess(true);
    setTimeout(() => {
      alert(`This would show your personalized ${cards[currentStep].title.toLowerCase()} dashboard!`);
    }, 500);
  };

  // Animate progress bar
  useEffect(() => {
    if (expanded && cards[currentStep].demoScore) {
      setTimeout(() => setProgress(cards[currentStep].demoScore), 300);
    } else {
      setProgress(0);
    }
  }, [expanded, currentStep]);

  // Animate success checkmark
  useEffect(() => {
    if (showSuccess) {
      const t = setTimeout(() => setShowSuccess(false), 1200);
      return () => clearTimeout(t);
    }
  }, [showSuccess]);

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

  const currentCard = cards[currentStep];
  const CurrentIcon = currentCard.icon;

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
                 className="text-4xl font-bold text-gray-900 mb-6">
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
            <div className="flex items-center justify-between text-base leading-relaxed text-gray-400 mb-2">
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
                <h2 id="accessibility-title" className="text-lg font-semibold text-white mb-3" className="text-2xl font-semibold text-gray-800 mb-4">
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
                    <span className="text-base leading-relaxed">High Contrast</span>
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
                    <span className="text-base leading-relaxed">Large Text</span>
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
                    <span className="text-base leading-relaxed">Screen Reader</span>
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
                    <span className="text-base leading-relaxed">Reduced Motion</span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <motion.div
            initial={{ x: 80, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 60, damping: 18 }}
            className="bg-gray-900 rounded-xl p-6 shadow-lg text-white max-w-lg mx-auto mb-6"
            role="region"
            aria-labelledby={`card-${currentStep}-title`}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 id={`card-${currentStep}-title`} className={`text-2xl font-bold ${currentCard.color}`} className="text-2xl font-semibold text-gray-800 mb-4">
                {currentCard.title}
              </h2>
              <motion.div
                animate={{ scale: [1, 1.15, 1] }}
                transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                aria-hidden="true"
              >
                <CurrentIcon className={`w-8 h-8 ${currentCard.color}`} />
              </motion.div>
            </div>
            
            <p className="mb-3 text-gray-200" style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}>
              {currentCard.description}
            </p>
            
            <ul className="mb-3 space-y-1" role="list">
              {currentCard.features.map((item, i) => (
                <li key={i} className="flex items-center" role="listitem">
                  <motion.span
                    initial={{ scale: 0.7 }}
                    animate={{ scale: expanded ? 1.2 : 1 }}
                    transition={{ type: "spring", stiffness: 300, damping: 10 }}
                    className="mr-2"
                    aria-hidden="true"
                  >
                    <CheckCircle className="text-green-400 w-4 h-4" />
                  </motion.span>
                  <span className="text-gray-200" style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}>
                    {item}
                  </span>
                </li>
              ))}
            </ul>

            <button
              className="text-blue-400 underline mb-2 text-base leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900 rounded"
              onClick={() => setExpanded(!expanded)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setExpanded(!expanded);
                }
              }}
              aria-expanded={expanded}
              aria-controls={`card-${currentStep}-details`}
              tabIndex={0}
              style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}
            >
              {expanded ? "Hide details" : "Tap to expand details"}
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  id={`card-${currentStep}-details`}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.4 }}
                  className="overflow-hidden"
                  role="region"
                  aria-labelledby={`card-${currentStep}-details-title`}
                >
                  {/* Animated Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center mb-1">
                      <span className="text-base leading-relaxed text-gray-400 mr-2">Demo Score</span>
                      <TrendingUp className="w-4 h-4 text-blue-400" aria-hidden="true" />
                    </div>
                    <div 
                      className="w-full bg-gray-700 rounded-full h-3"
                      role="progressbar"
                      aria-valuenow={progress}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${currentCard.title} score: ${progress} percent`}
                    >
                      <motion.div
                        className={`h-3 rounded-full ${currentCard.bgColor}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                      />
                    </div>
                    <span className={`font-bold ${currentCard.color}`}>{progress}%</span>
                  </div>

                  {/* Dynamic Content Based on Card Type */}
                  {currentStep === 1 && (
                    <div className="mb-4 p-3 bg-gray-800 rounded-lg">
                      <div className="text-base leading-relaxed text-gray-400 mb-3 text-center">Monthly Calendar Preview</div>
                      <div 
                        className="grid grid-cols-7 gap-1 mb-2"
                        role="grid"
                        aria-label="Monthly calendar showing important financial dates"
                      >
                        {Array.from({ length: 31 }, (_, i) => {
                          const day = i + 1;
                          const event = importantDates.find(d => d.day === day);
                          return (
                            <div
                              key={day}
                              className={`
                                w-6 h-6 rounded text-base leading-relaxed flex items-center justify-center relative
                                ${event ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}
                              `}
                              role="gridcell"
                              aria-label={event ? `${day}: ${event.label} - $${event.amount}` : `${day}`}
                            >
                              {day}
                              {event && (
                                <motion.div
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ delay: day * 0.05 }}
                                  className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full"
                                  aria-hidden="true"
                                />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Why it matters */}
                  <div className="mb-4">
                    <span className="block text-gray-400 font-semibold mb-1">Why it matters:</span>
                    <span className="text-gray-200" style={{ fontSize: accessibility.largeText ? '1.1rem' : undefined }}>
                      {currentStep === 0 && "Knowledge is power. When you understand your career landscape, you can make informed decisions that build wealth, not just pay bills. This helps you navigate challenges like job transitions, student loan repayment, or supporting family members with confidence."}
                      {currentStep === 1 && "Your money should work around your life, not the other way around. Plan for what matters most to you and your family - whether that's childcare, student loans, supporting parents, or building community. Take control of your financial future with confidence."}
                      {currentStep === 2 && "When you're stressed or exhausted, you spend differently. Understanding these patterns helps you build better money habits that stick. Whether you're managing family responsibilities, work stress, or financial pressures, taking care of your wellness is an investment in your financial future."}
                      {currentStep === 3 && "We know trust is earned. Your privacy isn't negotiable. When you're managing your family's financial future, you need to know your data is secure. We're committed to protecting your information with the same level of security that banks use."}
                    </span>
                  </div>

                  {/* Try It Button */}
                  <button
                    className={`${currentCard.bgColor} hover:opacity-90 text-white px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900`}
                    onClick={handleTryIt}
                    aria-describedby={`try-it-${currentStep}-description`}
                  >
                    Try It
                  </button>
                  <div id={`try-it-${currentStep}-description`} className="sr-only">
                    Opens your personalized {currentCard.title.toLowerCase()} dashboard
                  </div>

                  {/* Success checkmark */}
                  <AnimatePresence>
                    {showSuccess && (
                      <motion.div
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1.2, opacity: 1 }}
                        exit={{ scale: 0.5, opacity: 0 }}
                        transition={{ type: "spring", bounce: 0.7, duration: 0.6 }}
                        className="flex items-center mt-2"
                        role="status"
                        aria-live="polite"
                      >
                        <CheckCircle className="text-green-400 mr-2" aria-hidden="true" />
                        <span className="text-green-400 font-semibold">Success!</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Testimonial */}
            <div className="mt-4 text-base leading-relaxed text-gray-400 italic border-t border-gray-800 pt-2">
              <blockquote>
                <span>"{testimonials[currentCard.testimonialIndex % testimonials.length].quote}"</span>
                <footer className="block text-right text-gray-500 mt-1">
                  — {testimonials[currentCard.testimonialIndex % testimonials.length].author}
                </footer>
              </blockquote>
            </div>
          </motion.div>
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