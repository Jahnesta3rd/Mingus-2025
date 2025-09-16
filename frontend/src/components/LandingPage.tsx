import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, 
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
  DollarSign,
  TrendingDown,
  Zap
} from 'lucide-react';
import NavigationBar from './NavigationBar';
import ResponsiveTestComponent from './ResponsiveTestComponent';
import AssessmentModal, { AssessmentData } from './AssessmentModal';
import { ErrorBoundary } from './ErrorBoundary';
import { InputValidator } from '../utils/validation';
import { Sanitizer } from '../utils/sanitize';
import { runComprehensiveTest } from '../utils/responsiveTestUtils';

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
    icon: <Activity className="w-8 h-8" />,
    title: "Community Health Integration",
    description: "Track how your health choices impact your finances while addressing health disparities that affect our community's wealth-building potential."
  },
  {
    icon: <BarChart3 className="w-8 h-8" />,
    title: "Generational Wealth Forecasting",
    description: "Predict your financial future with AI-powered forecasting that accounts for systemic barriers and opportunities specific to Black professionals."
  },
  {
    icon: <Target className="w-8 h-8" />,
    title: "Black Excellence Milestones",
    description: "Set and achieve financial milestones with personalized roadmaps that honor our community's unique wealth-building journey and generational goals."
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
  const [openFAQ, setOpenFAQ] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [activeAssessment, setActiveAssessment] = useState<'ai-risk' | 'income-comparison' | 'cuffing-season' | 'layoff-risk' | null>(null);


  const toggleFAQ = (index: number) => {
    // Ensure only one FAQ item can be open at a time
    setOpenFAQ(openFAQ === index ? null : index);
  };

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleFAQ(index);
    }
  };

  // Enhanced keyboard navigation for assessment buttons
  const handleAssessmentKeyDown = (e: React.KeyboardEvent, assessmentType: string) => {
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

  // Enhanced keyboard navigation for section navigation
  const handleSectionKeyDown = (e: React.KeyboardEvent, sectionId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      scrollToSection(sectionId);
    }
  };

  const handleButtonClick = (action: string) => {
    setIsLoading(true);
    // Simulate loading state
    setTimeout(() => {
      setIsLoading(false);
      // Handle actual button action here
      console.log(`Button clicked: ${action}`);
    }, 1000);
  };

  // Handle assessment button clicks
  const handleAssessmentClick = (assessmentType: 'ai-risk' | 'income-comparison' | 'cuffing-season' | 'layoff-risk') => {
    setActiveAssessment(assessmentType);
    setIsLoading(false); // Stop loading state
  };

  // Handle assessment modal close
  const handleAssessmentClose = () => {
    setActiveAssessment(null);
  };

  // Handle assessment submission with security measures
  const handleAssessmentSubmit = async (data: AssessmentData) => {
    try {
      // Validate and sanitize data before sending
      const emailValidation = InputValidator.validateEmail(data.email);
      if (!emailValidation.isValid) {
        console.error('Email validation failed:', emailValidation.errors);
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

      // Show success message or redirect
      console.log('Assessment submitted successfully:', {
        assessmentType: sanitizedData.assessmentType,
        email: sanitizedData.email ? `${sanitizedData.email.substring(0, 3)}***@${sanitizedData.email.split('@')[1]}` : 'N/A',
        timestamp: new Date().toISOString()
      });
      
      // You can add success notification here
      // For now, we'll just close the modal
      setActiveAssessment(null);
      
    } catch (error) {
      console.error('Error submitting assessment:', error);
      // You can add error notification here
      // Don't log sensitive data in production
      if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
        console.error('Full error details:', error);
      }
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
    const timer = setTimeout(() => {
      runComprehensiveTest();
    }, 2000); // Wait for component to fully render

    return () => clearTimeout(timer);
  }, []);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-900 text-white">
        {/* Responsive Test Component - Remove in production */}
        <ResponsiveTestComponent />
      
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
        <section className="hero-section relative pt-16 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden" aria-label="Hero section">
        {/* Large Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-violet-900 to-purple-900"></div>
        
        <div className="relative max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Left Column - Text Content */}
            <div className="text-center lg:text-left">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 sm:mb-6 leading-tight">
                Financial Wellness Built
                <br />
                <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                  For Our Community
                </span>
              </h1>
              <p className="text-lg sm:text-xl md:text-2xl text-gray-300 mb-6 sm:mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                Empowering African American professionals to build generational wealth through intelligent financial planning, career advancement strategies, and wellness integration that honors our unique journey.
              </p>
              
              {/* Lead Magnet CTAs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6 sm:mb-8">
                <button 
                  onClick={() => handleAssessmentClick('ai-risk')}
                  onKeyDown={(e) => handleAssessmentKeyDown(e, 'ai-risk')}
                  disabled={isLoading}
                  aria-label="Determine Your Replacement Risk Due To AI"
                  aria-describedby="ai-replacement-risk-description"
                  className="group bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 disabled:from-violet-500 disabled:to-purple-500 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-lg text-base sm:text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-violet-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                  type="button"
                >
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white mr-2"></div>
                  )}
                  <span className="text-sm sm:text-base">
                    {isLoading ? 'Loading...' : 'Determine Your Replacement Risk Due To AI'}
                  </span>
                </button>
                <button 
                  onClick={() => handleAssessmentClick('income-comparison')}
                  onKeyDown={(e) => handleAssessmentKeyDown(e, 'income-comparison')}
                  disabled={isLoading}
                  aria-label="Determine How Your Income Compares"
                  aria-describedby="income-comparison-description"
                  className="group bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-purple-500 disabled:to-pink-500 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-lg text-base sm:text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-purple-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                  type="button"
                >
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white mr-2"></div>
                  )}
                  <span className="text-sm sm:text-base">
                    {isLoading ? 'Loading...' : 'Determine How Your Income Compares'}
                  </span>
                </button>
                <button 
                  onClick={() => handleAssessmentClick('cuffing-season')}
                  onKeyDown={(e) => handleAssessmentKeyDown(e, 'cuffing-season')}
                  disabled={isLoading}
                  aria-label="Determine Your Cuffing Season Score"
                  aria-describedby="cuffing-season-description"
                  className="group bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-700 hover:to-rose-700 disabled:from-pink-500 disabled:to-rose-500 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-lg text-base sm:text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-pink-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-pink-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                  type="button"
                >
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white mr-2"></div>
                  )}
                  <span className="text-sm sm:text-base">
                    {isLoading ? 'Loading...' : 'Determine Your "Cuffing Season" Score'}
                  </span>
                </button>
                <button 
                  onClick={() => handleAssessmentClick('layoff-risk')}
                  onKeyDown={(e) => handleAssessmentKeyDown(e, 'layoff-risk')}
                  disabled={isLoading}
                  aria-label="Determine Your Layoff Risk"
                  aria-describedby="layoff-risk-description"
                  className="group bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-700 hover:to-red-700 disabled:from-rose-500 disabled:to-red-500 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-lg text-base sm:text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-rose-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-rose-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                  type="button"
                >
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white mr-2"></div>
                  )}
                  <span className="text-sm sm:text-base">
                    {isLoading ? 'Loading...' : 'Determine Your Layoff Risk'}
                  </span>
                </button>
              </div>
              
              
              {/* Hidden descriptions for accessibility */}
              <div className="sr-only">
                <div id="ai-replacement-risk-description">
                  Determine your replacement risk due to AI with our comprehensive assessment tool that analyzes your job security in the age of artificial intelligence.
                </div>
                <div id="income-comparison-description">
                  Determine how your income compares to others in your field and location with our detailed salary analysis and benchmarking tools.
                </div>
                <div id="cuffing-season-description">
                  Determine your "Cuffing Season" score with our fun and insightful relationship assessment that analyzes your dating and relationship patterns.
                </div>
                <div id="layoff-risk-description">
                  Determine your layoff risk with our comprehensive job security assessment that analyzes industry trends, company stability, and your personal risk factors.
                </div>
              </div>
            </div>
            
            {/* Right Column - App Preview Mockup */}
            <div className="flex justify-center lg:justify-end mt-8 lg:mt-0">
              <div className="relative">
                {/* Phone Mockup Container */}
                <div className="w-72 sm:w-80 h-80 sm:h-96 bg-gray-800 rounded-3xl p-3 sm:p-4 shadow-2xl">
                  <div className="w-full h-full bg-gradient-to-br from-violet-900 to-purple-900 rounded-2xl p-4 sm:p-6 flex flex-col space-y-3 sm:space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <h2 className="text-white font-bold text-base sm:text-lg">Mingus</h2>
                      <div className="w-6 h-6 sm:w-8 sm:h-8 bg-violet-500 rounded-full flex items-center justify-center">
                        <Heart className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                      </div>
                    </div>
                    
                    {/* Cards */}
                    <div className="space-y-2 sm:space-y-3 flex-1">
                      {/* Wellness Score Card */}
                      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-violet-400/20">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <Heart className="w-4 h-4 sm:w-5 sm:h-5 text-violet-300 mr-2" />
                            <span className="text-white font-semibold text-sm sm:text-base">Wellness Score</span>
                          </div>
                          <span className="text-violet-300 text-xs sm:text-sm">85%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5 sm:h-2">
                          <div className="bg-gradient-to-r from-violet-400 to-purple-400 h-1.5 sm:h-2 rounded-full" style={{width: '85%'}}></div>
                        </div>
                      </div>
                      
                      {/* Cash Flow Card */}
                      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-violet-400/20">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-violet-300 mr-2" />
                            <span className="text-white font-semibold text-sm sm:text-base">Cash Flow</span>
                          </div>
                          <span className="text-green-400 text-xs sm:text-sm">+$2,340</span>
                        </div>
                        <div className="text-white text-xs opacity-75">This month vs last</div>
                      </div>
                      
                      {/* Next Milestone Card */}
                      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-violet-400/20">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-violet-300 mr-2" />
                            <span className="text-white font-semibold text-sm sm:text-base">Next Milestone</span>
                          </div>
                          <span className="text-violet-300 text-xs sm:text-sm">$5K</span>
                        </div>
                        <div className="text-white text-xs opacity-75">Emergency Fund • 67% complete</div>
                      </div>
                    </div>
                    
                    {/* Bottom Action */}
                    <button className="w-full bg-gradient-to-r from-violet-500 to-purple-500 text-white py-2 sm:py-3 rounded-xl font-semibold text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800">
                      View Full Dashboard
                    </button>
                  </div>
                </div>
                
                {/* Floating Elements */}
                <div className="absolute -top-2 -right-2 sm:-top-4 sm:-right-4 w-6 h-6 sm:w-8 sm:h-8 bg-violet-500 rounded-full flex items-center justify-center animate-pulse">
                  <Star className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <div className="absolute -bottom-2 -left-2 sm:-bottom-4 sm:-left-4 w-4 h-4 sm:w-6 sm:h-6 bg-purple-500 rounded-full flex items-center justify-center animate-bounce">
                  <Check className="w-2 h-2 sm:w-3 sm:h-3 text-white" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Assessment Section */}
      <section aria-labelledby="assessments-heading" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900" role="region">
        <div className="max-w-7xl mx-auto">
          <h2 id="assessments-heading" className="text-3xl md:text-4xl font-bold mb-4 text-center">
            Choose Your Assessment
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto text-center mb-12">
            Take our specialized assessments to understand your financial position and opportunities for growth.
          </p>
          
          {/* Assessment Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" role="list" aria-label="Assessment options">
            {/* AI Risk Assessment Card */}
            <div className="group bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-violet-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-violet-500/20 hover:-translate-y-2" role="listitem">
              <div className="text-violet-400 mb-4 group-hover:text-violet-300 transition-all duration-300 transform group-hover:scale-110" aria-hidden="true">
                <Heart className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-white group-hover:text-violet-100 transition-colors duration-300">
                AI Replacement Risk
              </h3>
              <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed mb-4">
                Determine your replacement risk due to AI with our comprehensive assessment tool.
              </p>
              <button 
                onClick={() => handleAssessmentClick('ai-risk')}
                onKeyDown={(e) => handleAssessmentKeyDown(e, 'ai-risk')}
                disabled={isLoading}
                aria-label="Take AI Replacement Risk Assessment"
                className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-violet-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                type="button"
              >
                {isLoading ? 'Loading...' : 'Take Assessment'}
              </button>
            </div>

            {/* Income Comparison Card */}
            <div className="group bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-purple-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/20 hover:-translate-y-2" role="listitem">
              <div className="text-purple-400 mb-4 group-hover:text-purple-300 transition-all duration-300 transform group-hover:scale-110" aria-hidden="true">
                <TrendingUp className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-white group-hover:text-purple-100 transition-colors duration-300">
                Income Comparison
              </h3>
              <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed mb-4">
                See how your income compares to others in your field and location.
              </p>
              <button 
                onClick={() => handleAssessmentClick('income-comparison')}
                onKeyDown={(e) => handleAssessmentKeyDown(e, 'income-comparison')}
                disabled={isLoading}
                aria-label="Take Income Comparison Assessment"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-purple-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                type="button"
              >
                {isLoading ? 'Loading...' : 'Take Assessment'}
              </button>
            </div>

            {/* Cuffing Season Card */}
            <div className="group bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-pink-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-pink-500/20 hover:-translate-y-2" role="listitem">
              <div className="text-pink-400 mb-4 group-hover:text-pink-300 transition-all duration-300 transform group-hover:scale-110" aria-hidden="true">
                <Calendar className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-white group-hover:text-pink-100 transition-colors duration-300">
                Cuffing Season Score
              </h3>
              <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed mb-4">
                Determine your "Cuffing Season" score with our fun relationship assessment.
              </p>
              <button 
                onClick={() => handleAssessmentClick('cuffing-season')}
                onKeyDown={(e) => handleAssessmentKeyDown(e, 'cuffing-season')}
                disabled={isLoading}
                aria-label="Take Cuffing Season Score Assessment"
                className="w-full bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-700 hover:to-rose-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-pink-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-pink-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                type="button"
              >
                {isLoading ? 'Loading...' : 'Take Assessment'}
              </button>
            </div>

            {/* Layoff Risk Card */}
            <div className="group bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-rose-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-rose-500/20 hover:-translate-y-2" role="listitem">
              <div className="text-rose-400 mb-4 group-hover:text-rose-300 transition-all duration-300 transform group-hover:scale-110" aria-hidden="true">
                <Target className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-white group-hover:text-rose-100 transition-colors duration-300">
                Layoff Risk Assessment
              </h3>
              <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed mb-4">
                Assess your job security with our comprehensive layoff risk analysis.
              </p>
              <button 
                onClick={() => handleAssessmentClick('layoff-risk')}
                onKeyDown={(e) => handleAssessmentKeyDown(e, 'layoff-risk')}
                disabled={isLoading}
                aria-label="Take Layoff Risk Assessment"
                className="w-full bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-700 hover:to-red-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-rose-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-rose-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
                type="button"
              >
                {isLoading ? 'Loading...' : 'Take Assessment'}
              </button>
            </div>
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
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800/50" role="region" aria-label="Features">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to Manage Your Money
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Powerful features designed to help you understand, track, and improve your financial health.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                <div className="text-purple-400 mb-4 group-hover:text-purple-300 transition-all duration-300 transform group-hover:scale-110">
                  {feature.icon}
                </div>
                <h2 className="text-xl font-semibold mb-3 group-hover:text-purple-100 transition-colors duration-300">{feature.title}</h2>
                <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

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
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800/50" role="region" aria-label="Pricing plans">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Choose Your Plan
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Start free and upgrade as you grow. All plans include our core features.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingTiers.map((tier, index) => (
              <div key={index} className={`group bg-gray-800 p-8 rounded-xl relative transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-violet-500/20 hover:-translate-y-2 ${tier.popular ? 'ring-2 ring-violet-500 hover:ring-violet-400' : 'hover:ring-2 hover:ring-violet-500/50'}`}>
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-violet-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2 text-white group-hover:text-violet-100 transition-colors duration-300">{tier.name}</h2>
                  <div className="mb-2">
                    <span className="text-4xl font-bold text-violet-400 group-hover:text-violet-300 transition-colors duration-300">{tier.price}</span>
                    <span className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">/{tier.period}</span>
                  </div>
                  <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{tier.description}</p>
                </div>
                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start group-hover:translate-x-1 transition-transform duration-300" style={{transitionDelay: `${featureIndex * 50}ms`}}>
                      <Check className="w-5 h-5 text-violet-400 mt-0.5 mr-3 flex-shrink-0 group-hover:text-violet-300 transition-colors duration-300" />
                      <span className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button className={`w-full py-3 px-6 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                  tier.popular 
                    ? 'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white shadow-lg hover:shadow-violet-500/25' 
                    : 'border-2 border-violet-500 text-violet-400 hover:bg-violet-500 hover:text-white hover:shadow-lg hover:shadow-violet-500/25'
                }`}>
                  {tier.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-slate-900 to-slate-800" role="region" aria-label="Frequently asked questions">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-300">
              Everything you need to know about Mingus
            </p>
          </div>
          
          <div className="space-y-4 sm:space-y-6">
            {faqData.map((faq, index) => (
              <div 
                key={index} 
                className={`bg-slate-800/80 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-xl transition-all duration-300 hover:border-violet-500/30 hover:bg-slate-800/90 hover:shadow-2xl hover:shadow-violet-500/10 ${
                  openFAQ === index ? 'ring-2 ring-violet-500/50 shadow-2xl shadow-violet-500/20' : ''
                }`}
              >
                <button
                  className="w-full px-4 sm:px-6 py-4 sm:py-5 text-left flex justify-between items-center hover:bg-slate-700/30 transition-all duration-300 rounded-xl group focus-ring focus-visible:ring-4 focus-visible:ring-violet-500 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
                  onClick={() => toggleFAQ(index)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  aria-expanded={openFAQ === index}
                  aria-controls={`faq-answer-${index}`}
                  id={`faq-question-${index}`}
                  tabIndex={0}
                >
                  <span className="font-semibold text-gray-100 group-hover:text-violet-300 transition-colors duration-300 pr-4 text-sm sm:text-base">
                    {faq.question}
                  </span>
                  <div className="flex-shrink-0">
                    <div className={`transform transition-all duration-300 ease-in-out ${
                      openFAQ === index ? 'rotate-180 scale-110' : 'rotate-0 scale-100'
                    }`}>
                      <ChevronDown className="w-4 h-4 sm:w-5 sm:h-5 text-violet-400 group-hover:text-violet-300 transition-colors duration-300" />
                    </div>
                  </div>
                </button>
                <div 
                  id={`faq-answer-${index}`}
                  role="region"
                  aria-labelledby={`faq-question-${index}`}
                  className={`overflow-hidden transition-all duration-500 ease-in-out ${
                    openFAQ === index 
                      ? 'max-h-96 opacity-100' 
                      : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="px-4 sm:px-6 pb-4 sm:pb-5 pt-2">
                    <div className="border-t border-slate-700/50 pt-4">
                      <p className="text-gray-300 leading-relaxed text-sm sm:text-base">
                        {faq.answer}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-violet-600 via-violet-700 to-purple-800" role="region" aria-label="Call to action">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6 text-white">
            Ready to Build Generational Wealth?
          </h2>
          <p className="text-xl text-violet-100 mb-10 max-w-2xl mx-auto">
            Join thousands of Black professionals who are building wealth while maintaining wellness with Mingus.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={() => handleButtonClick('Start Your Wealth Journey')}
              onKeyDown={(e) => handleCTAKeyDown(e, 'Start Your Wealth Journey')}
              disabled={isLoading}
              aria-label="Start your wealth building journey with Mingus"
              className="group bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 disabled:from-violet-400 disabled:to-purple-500 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 transform hover:scale-105 flex items-center shadow-lg hover:shadow-xl hover:shadow-violet-500/25 hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-violet-800"
            >
              {isLoading && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              )}
              {isLoading ? 'Loading...' : 'Start Your Wealth Journey'}
            </button>
            <button
              onClick={() => handleButtonClick('Join Our Community')}
              onKeyDown={(e) => handleCTAKeyDown(e, 'Join Our Community')}
              disabled={isLoading}
              aria-label="Join our community of Black professionals"
              className="group border-2 border-white text-white hover:bg-white hover:text-violet-600 disabled:border-gray-400 disabled:text-gray-400 px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-white/25 hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-white focus-visible:ring-offset-4 focus-visible:ring-offset-violet-800"
            >
              {isLoading ? 'Loading...' : 'Join Our Community'}
            </button>
          </div>
          <p className="text-sm text-violet-200 mt-6">
            Free assessments • No commitment required • Start your journey today
          </p>
        </div>
      </section>
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

      {/* Assessment Modal */}
      <AssessmentModal
        isOpen={activeAssessment !== null}
        assessmentType={activeAssessment}
        onClose={handleAssessmentClose}
        onSubmit={handleAssessmentSubmit}
      />
      </div>
    </ErrorBoundary>
  );
};

export default LandingPage;
