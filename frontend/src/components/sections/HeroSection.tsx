import React from 'react';
import { Heart, TrendingUp, Calendar, Star, Check } from 'lucide-react';
import { AssessmentType } from '../../types/assessments';

interface HeroSectionProps {
  onAssessmentClick: (assessmentType: AssessmentType) => void;
  onAssessmentKeyDown: (e: React.KeyboardEvent, assessmentType: AssessmentType) => void;
  isLoading: boolean;
  navigate: (path: string) => void;
}

const HeroSection: React.FC<HeroSectionProps> = ({
  onAssessmentClick,
  onAssessmentKeyDown,
  isLoading,
  navigate
}) => {
  // Smooth scroll function for anchor navigation
  const scrollToAssessment = (assessmentType: AssessmentType) => {
    const element = document.getElementById('assessments');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Open the assessment modal after scrolling completes
      setTimeout(() => {
        onAssessmentClick(assessmentType);
      }, 600);
    } else {
      // Fallback: if element not found, open modal directly
      onAssessmentClick(assessmentType);
    }
  };

  // Keyboard handler that also uses scroll navigation
  const handleKeyDown = (e: React.KeyboardEvent, assessmentType: AssessmentType) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      scrollToAssessment(assessmentType);
    }
  };

  return (
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
                onClick={() => scrollToAssessment('ai-risk')}
                onKeyDown={(e) => handleKeyDown(e, 'ai-risk')}
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
                onClick={() => scrollToAssessment('income-comparison')}
                onKeyDown={(e) => handleKeyDown(e, 'income-comparison')}
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
                onClick={() => scrollToAssessment('cuffing-season')}
                onKeyDown={(e) => handleKeyDown(e, 'cuffing-season')}
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
                onClick={() => scrollToAssessment('layoff-risk')}
                onKeyDown={(e) => handleKeyDown(e, 'layoff-risk')}
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
                  <button 
                    onClick={() => navigate('/signup?source=cta')}
                    className="w-full bg-gradient-to-r from-violet-500 to-purple-500 text-white py-2 sm:py-3 rounded-xl font-semibold text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800"
                    aria-label="Get started with Mingus"
                  >
                    Get Started
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
  );
};

export default HeroSection;

