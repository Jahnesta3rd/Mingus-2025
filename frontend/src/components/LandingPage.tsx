import React, { useState, useEffect } from 'react';
import { 
  Check, 
  Star, 
  Shield, 
  TrendingUp, 
  Smartphone, 
  CreditCard, 
  PieChart, 
  Target, 
  ChevronDown,
  Heart,
  Calendar,
  Activity,
  BarChart3,
  Briefcase,
  TrendingDown,
  Zap,
  Car
} from 'lucide-react';
import NavigationBar from './NavigationBar';
import ResponsiveTestComponent from './ResponsiveTestComponent';
import AssessmentModal, { AssessmentData } from './AssessmentModal';
import { ErrorBoundary } from './ErrorBoundary';
import ModalErrorFallback from './ModalErrorFallback';
import { InputValidator } from '../utils/validation';
import { Sanitizer } from '../utils/sanitize';
import { runComprehensiveTest } from '../utils/responsiveTestUtils';
import { logger } from '../utils/logger';
import { useNavigate } from 'react-router-dom';
import { AssessmentType } from '../types/assessments';
import { useAnalytics } from '../hooks/useAnalytics';
import HeroSection from './sections/HeroSection';
import AssessmentSection from './sections/AssessmentSection';
import FeaturesSection from './sections/FeaturesSection';
import PricingSection from './sections/PricingSection';
import FAQSection from './sections/FAQSection';
import CTASection from './sections/CTASection';

// Types
interface FAQItem {
  question: string;
  answer: string;
}

interface PricingTier {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  popular?: boolean;
  cta: string;
}

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
}

// FAQ Data
const faqData: FAQItem[] = [
  {
    question: "How does Mingus address the unique financial challenges faced by African American professionals?",
    answer: "Mingus is specifically designed to address systemic barriers and opportunities in our community. We integrate health data to understand how financial stress affects our well-being, while providing culturally-aware financial planning that accounts for generational wealth gaps, workplace dynamics, and community-specific investment opportunities."
  },
  {
    question: "What makes Mingus different from other finance apps for Black professionals?",
    answer: "Unlike traditional budgeting apps, Mingus understands the unique financial journey of African American professionals. We provide contextual advice based on our community's specific challenges, generational wealth building goals, and cultural values. Our AI is trained on data that reflects our community's financial patterns and opportunities."
  },
  {
    question: "How does Mingus help with career advancement and salary negotiations?",
    answer: "Mingus offers specialized career guidance that addresses workplace dynamics and bias while providing strategic financial planning. We help you navigate salary negotiations, career moves, and wealth-building opportunities while understanding the unique challenges Black professionals face in corporate environments."
  },
  {
    question: "Can Mingus help me build generational wealth for my family?",
    answer: "Absolutely! Mingus is specifically designed to help break generational financial barriers. We provide tools for estate planning, investment strategies, and wealth transfer planning that honor our community's values while building lasting financial security for future generations."
  },
  {
    question: "How does Mingus address health disparities that affect our community's financial wellness?",
    answer: "Mingus integrates health data to understand how systemic health disparities impact our financial wellness. We provide personalized recommendations that address both physical and mental health while building wealth, recognizing the interconnected nature of health and financial stability in our community."
  },
  {
    question: "Is my financial data secure and private with Mingus?",
    answer: "Your data security and privacy are our top priorities. We use bank-level 256-bit encryption, multi-factor authentication, and are SOC 2 Type II certified. Your data is never sold or shared without explicit consent, and we regularly undergo third-party security audits to ensure the highest protection standards for our community."
  }
];

// Pricing Data
const pricingTiers: PricingTier[] = [
  {
    name: "Budget",
    price: "$15",
    period: "per month",
    description: "Perfect for getting started with basic financial tracking",
    features: [
      "Basic expense tracking",
      "Up to 3 budgets",
      "Monthly financial reports",
      "Mobile app access",
      "Email support"
    ],
    cta: "Get Started"
  },
  {
    name: "Mid-tier",
    price: "$35",
    period: "per month",
    description: "Advanced features for serious money management",
    features: [
      "Unlimited budgets & categories",
      "Advanced analytics & insights",
      "Bill reminders & notifications",
      "Investment tracking",
      "Priority customer support",
      "Custom financial goals",
      "Export data to Excel/PDF"
    ],
    popular: true,
    cta: "Start Free Trial"
  },
  {
    name: "Professional",
    price: "$100",
    period: "per month",
    description: "Complete financial management suite",
    features: [
      "Everything in Mid-tier",
      "Tax preparation tools",
      "Financial advisor consultations",
      "Advanced investment analysis",
      "Family account management",
      "API access for integrations",
      "White-label options"
    ],
    cta: "Go Professional"
  }
];

// Features Data
const features: Feature[] = [
  {
    icon: <TrendingUp className="w-8 h-8" />,
    title: "Smart Analytics",
    description: "AI-powered insights help you understand your spending patterns and identify opportunities to save money."
  },
  {
    icon: <Shield className="w-8 h-8" />,
    title: "Bank-Level Security",
    description: "Your financial data is protected with military-grade encryption and never shared without your consent."
  },
  {
    icon: <Smartphone className="w-8 h-8" />,
    title: "Mobile-First Design",
    description: "Access your finances anywhere with our intuitive mobile app available on iOS and Android."
  },
  {
    icon: <CreditCard className="w-8 h-8" />,
    title: "Expense Tracking",
    description: "Automatically categorize and track all your expenses with smart categorization and receipt scanning."
  },
  {
    icon: <PieChart className="w-8 h-8" />,
    title: "Budget Management",
    description: "Create unlimited budgets, set spending limits, and get real-time alerts when you're approaching limits."
  },
  {
    icon: <Target className="w-8 h-8" />,
    title: "Goal Setting",
    description: "Set and track financial goals with personalized recommendations to help you achieve them faster."
  }
];

// Financial Wellness Features Data
const financialWellnessFeatures: Feature[] = [
  {
    icon: <BarChart3 className="w-8 h-8" />,
    title: "Generational Wealth Forecasting",
    description: "Predict your financial future with AI-powered forecasting that accounts for systemic barriers and opportunities specific to Black professionals."
  },
  {
    icon: <Target className="w-8 h-8" />,
    title: "Wealth Milestones",
    description: "Set and achieve financial milestones with personalized roadmaps unique to the legacy that you want to build."
  },
  {
    icon: <Briefcase className="w-8 h-8" />,
    title: "Career Advancement Strategies",
    description: "Get strategic advice on salary negotiations, career moves, and wealth-building opportunities while navigating workplace dynamics and bias."
  },
  {
    icon: <TrendingDown className="w-8 h-8" />,
    title: "Economic Resilience Planning",
    description: "Monitor and mitigate career risks with real-time analysis of economic trends and job market stability that impact our community."
  },
  {
    icon: <Zap className="w-8 h-8" />,
    title: "Holistic Wellness-Finance",
    description: "Connect your physical, mental, and spiritual wellness goals with your financial planning, honoring our community's values and traditions."
  }
];

// Main Landing Page Component
const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { trackInteraction, trackPageView } = useAnalytics();
  const [openFAQ, setOpenFAQ] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [activeAssessment, setActiveAssessment] = useState<AssessmentType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Track page view on mount
  useEffect(() => {
    trackPageView('/landing', { page_type: 'landing_page' });
  }, [trackPageView]);


  const toggleFAQ = (index: number) => {
    // Ensure only one FAQ item can be open at a time
    const newState = openFAQ === index ? null : index;
    setOpenFAQ(newState);
    
    // Track FAQ interaction
    trackInteraction('faq_toggle', {
      faq_index: index,
      action: newState === null ? 'close' : 'open',
      page: 'landing'
    });
  };

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleFAQ(index);
    }
  };

  // Enhanced keyboard navigation for assessment buttons
  const handleAssessmentKeyDown = (e: React.KeyboardEvent, assessmentType: AssessmentType) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleAssessmentClick(assessmentType);
    }
  };

  // Enhanced keyboard navigation for CTA buttons
  const handleCTAKeyDown = (e: React.KeyboardEvent, buttonText: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleButtonClick(buttonText);
    }
  };


  const handleButtonClick = (action: string) => {
    // Track button click
    trackInteraction('button_click', {
      button_name: action,
      page: 'landing'
    });
    
    // Navigate to signup page
    navigate('/signup');
  };

  // Handle assessment button clicks
  const handleAssessmentClick = (assessmentType: AssessmentType) => {
    // Track assessment started
    trackInteraction('assessment_started', {
      assessment_type: assessmentType,
      page: 'landing'
    });
    
    setActiveAssessment(assessmentType);
    setIsLoading(false); // Stop loading state
  };

  // Handle assessment modal close
  const handleAssessmentClose = () => {
    // Track assessment modal closed
    if (activeAssessment) {
      trackInteraction('assessment_closed', {
        assessment_type: activeAssessment,
        page: 'landing'
      });
    }
    setActiveAssessment(null);
  };

  // Handle assessment submission with security measures
  const handleAssessmentSubmit = async (data: AssessmentData) => {
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);
    
    try {
      // Validate and sanitize data before sending
      const emailValidation = InputValidator.validateEmail(data.email);
      if (!emailValidation.isValid) {
        const errorMessage = emailValidation.errors.join(', ') || 'Invalid email address';
        setError(errorMessage);
        logger.error('Email validation failed:', emailValidation.errors);
        setIsSubmitting(false);
        return;
      }

      // Sanitize all string data
      const sanitizedData = {
        ...data,
        email: emailValidation.sanitizedValue!,
        firstName: data.firstName ? Sanitizer.sanitizeString(data.firstName) : undefined,
        phone: data.phone ? Sanitizer.sanitizeString(data.phone) : undefined,
        answers: Sanitizer.sanitizeObject(data.answers)
      };

      // Get CSRF token from meta tag or cookie
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                       getCookie('csrf-token') || '';

      // Send assessment data to API with security headers
      const response = await fetch('/api/assessments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'include',
        body: JSON.stringify(sanitizedData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: Failed to submit assessment`);
      }

      // Track successful assessment submission
      trackInteraction('assessment_submitted', {
        assessment_type: sanitizedData.assessmentType,
        page: 'landing',
        success: true
      });
      
      // Show success message
      setSuccess('Assessment submitted successfully!');
      logger.log('Assessment submitted successfully:', {
        assessmentType: sanitizedData.assessmentType,
        email: sanitizedData.email ? `${sanitizedData.email.substring(0, 3)}***@${sanitizedData.email.split('@')[1]}` : 'N/A',
        timestamp: new Date().toISOString()
      });
      
      // Close the modal after a short delay
      setTimeout(() => {
        setActiveAssessment(null);
      }, 1500);
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to submit assessment. Please try again.';
      
      // Track assessment submission error
      trackInteraction('assessment_submission_error', {
        assessment_type: data.assessmentType,
        page: 'landing',
        error: errorMessage,
        success: false
      });
      
      setError(errorMessage);
      setIsSubmitting(false);
      logger.error('Error submitting assessment:', error);
      // Don't log sensitive data in production
      if (import.meta.env.DEV) {
        logger.error('Full error details:', error);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper function to get cookie value
  const getCookie = (name: string): string => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift() || '';
    }
    return '';
  };

  // Run comprehensive test on component mount
  useEffect(() => {
    // Only run comprehensive test in development
    if (import.meta.env.DEV) {
      let isMounted = true;
      const timer = setTimeout(() => {
        // Only run test if component is still mounted
        if (isMounted) {
          runComprehensiveTest();
        }
      }, 2000); // Wait for component to fully render

      return () => {
        // Cleanup: clear timer and mark as unmounted
        clearTimeout(timer);
        isMounted = false;
      };
    }
  }, []);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-900 text-white">
        {/* Responsive Test Component - Only in development */}
        {import.meta.env.DEV && <ResponsiveTestComponent />}
      
      {/* Skip Links for Accessibility */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-violet-600 text-white px-4 py-2 rounded-lg z-50"
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
        {/* Hero Section */}
        <HeroSection
          onAssessmentClick={handleAssessmentClick}
          onAssessmentKeyDown={handleAssessmentKeyDown}
          isLoading={isLoading}
          navigate={navigate}
        />
        
        {/* Risk Assessment Preview Section - Only shows preview, not actual results */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gray-900" role="region" aria-label="Career risk assessment preview">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-white">
              Understand Your Career Risk
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
              Get personalized risk assessments and career protection recommendations based on your industry, role, and market conditions.
            </p>
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
              <div className="flex items-center justify-center gap-3 mb-4">
                <Shield className="h-8 w-8" />
                <h3 className="text-2xl font-semibold">Risk Assessment Preview</h3>
              </div>
              <p className="text-lg mb-6 text-blue-100">
                Subscribe to unlock your personalized career risk analysis and get actionable recommendations to protect your career.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => setActiveAssessment('ai-risk')}
                  className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 rounded-lg px-6 py-3 text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/50"
                  aria-label="Start free AI replacement risk assessment"
                >
                  Start Free Assessment
                </button>
                <button
                  onClick={() => navigate('/signup')}
                  className="bg-white text-blue-600 hover:bg-gray-100 rounded-lg px-6 py-3 text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/50"
                  aria-label="Get started with Mingus"
                >
                  Get Started
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Assessment Section */}
      <AssessmentSection
        onAssessmentClick={handleAssessmentClick}
        onAssessmentKeyDown={handleAssessmentKeyDown}
        isLoading={isLoading}
      />

      {/* Job Recommendations Preview Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" role="region" aria-label="Job recommendations preview">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900">
              Personalized Job Recommendations
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Get three-tier job recommendations based on your risk assessment and career goals.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Conservative Tier Preview */}
            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 text-center">
              <div className="text-blue-600 mb-4">
                <Shield className="h-8 w-8 mx-auto" />
              </div>
              <h3 className="text-lg font-semibold text-blue-600 mb-2">Safe Growth</h3>
              <p className="text-sm text-gray-600 mb-4">15-20% salary increase, high success probability</p>
              <div className="text-xs text-gray-500">Subscribe to see your personalized recommendations</div>
            </div>
            
            {/* Optimal Tier Preview */}
            <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-6 text-center ring-2 ring-purple-300 shadow-lg">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <div className="bg-purple-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                  RECOMMENDED
                </div>
              </div>
              <div className="text-purple-600 mb-4">
                <Target className="h-8 w-8 mx-auto" />
              </div>
              <h3 className="text-lg font-semibold text-purple-600 mb-2">Strategic Advance</h3>
              <p className="text-sm text-gray-600 mb-4">25-30% salary increase, moderate stretch</p>
              <div className="text-xs text-gray-500">Subscribe to see your personalized recommendations</div>
            </div>
            
            {/* Stretch Tier Preview */}
            <div className="bg-orange-50 border-2 border-dashed border-orange-200 rounded-xl p-6 text-center">
              <div className="text-orange-600 mb-4">
                <Zap className="h-8 w-8 mx-auto" />
              </div>
              <h3 className="text-lg font-semibold text-orange-600 mb-2">Ambitious Leap</h3>
              <p className="text-sm text-gray-600 mb-4">35%+ salary increase, significant growth</p>
              <div className="text-xs text-gray-500">Subscribe to see your personalized recommendations</div>
            </div>
          </div>
          
          <div className="text-center mt-8">
            <button
              onClick={() => navigate('/signup')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Get started with Mingus to access job recommendations"
            >
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* Financial Wellness Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900" role="region" aria-label="Financial wellness features">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Financial Wellness
              <br />
              <span className="text-violet-400">For Our Community</span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Comprehensive financial tools designed specifically for African American professionals, addressing the unique challenges and opportunities in our community's wealth-building journey.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {financialWellnessFeatures.map((feature, index) => (
              <div 
                key={index} 
                className="group bg-gradient-to-br from-slate-800 to-slate-900 p-8 rounded-xl border border-slate-700 hover:border-violet-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-violet-500/20 hover:-translate-y-2"
                onMouseEnter={() => setHoveredCard(index)}
                onMouseLeave={() => setHoveredCard(null)}
              >
                <div className="text-violet-400 mb-6 group-hover:text-violet-300 transition-all duration-300 transform group-hover:scale-110">
                  {feature.icon}
                </div>
                <h2 className="text-xl font-semibold mb-4 text-white group-hover:text-violet-100 transition-colors duration-300">
                  {feature.title}
                </h2>
                <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed">
                  {feature.description}
                </p>
                {hoveredCard === index && (
                  <div className="mt-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="w-full h-1 bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <FeaturesSection features={features} />
      
      {/* Value Proposition Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden" role="region" aria-label="Value proposition and success stories">
        {/* Violet Gradient Background Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900/90 via-purple-900/80 to-violet-800/90"></div>
        
        <div className="relative max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Heading, Description, and Stats */}
            <div className="text-center lg:text-left">
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                Build Generational Wealth
                <br />
                <span className="bg-gradient-to-r from-violet-300 to-purple-300 bg-clip-text text-transparent">
                  For Our Future
                </span>
              </h2>
              <p className="text-xl md:text-2xl text-gray-200 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                Transform your relationship with money through intelligent financial planning, 
                wellness integration, and personalized wealth-building strategies that honor our 
                community's unique journey and break generational financial barriers.
              </p>
              
            </div>
            
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <PricingSection pricingTiers={pricingTiers} navigate={navigate} />
      
      {/* FAQ Section */}
      <FAQSection
        faqData={faqData}
        openFAQ={openFAQ}
        onToggleFAQ={toggleFAQ}
        onKeyDown={handleKeyDown}
      />
      
      {/* CTA Section */}
      <CTASection
        onButtonClick={handleButtonClick}
        onCTAKeyDown={handleCTAKeyDown}
        isLoading={isLoading}
        navigate={navigate}
      />
      
      {/* Footer */}
      <footer id="footer" className="bg-gray-900 border-t border-gray-800 py-12 px-4 sm:px-6 lg:px-8" role="contentinfo" aria-label="Site footer">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-400">
            © {new Date().getFullYear()} Mingus. All rights reserved.
          </p>
        </div>
      </footer>
      </main>


      {/* Assessment Modal with Error Boundary */}
      <ErrorBoundary 
        fallback={
          <ModalErrorFallback 
            onClose={handleAssessmentClose}
            onRetry={() => {
              // Reset error boundary by closing and reopening modal
              handleAssessmentClose();
              // Small delay to allow error boundary to reset
              setTimeout(() => {
                if (activeAssessment) {
                  // Reopen the same assessment
                  setActiveAssessment(activeAssessment);
                }
              }, 100);
            }}
          />
        }
      >
        <AssessmentModal
          isOpen={activeAssessment !== null}
          assessmentType={activeAssessment}
          onClose={handleAssessmentClose}
          onSubmit={handleAssessmentSubmit}
          isSubmitting={isSubmitting}
        />
      </ErrorBoundary>

      {/* Error Message */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md transform transition-all duration-300 ease-in-out">
          <div className="flex items-center justify-between">
            <span className="flex-1">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="ml-4 text-white hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-white/50 rounded p-1"
              aria-label="Close error message"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md transform transition-all duration-300 ease-in-out">
          <div className="flex items-center justify-between">
            <span className="flex-1">{success}</span>
            <button 
              onClick={() => setSuccess(null)}
              className="ml-4 text-white hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-white/50 rounded p-1"
              aria-label="Close success message"
            >
              ×
            </button>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  );
};

export default LandingPage;
