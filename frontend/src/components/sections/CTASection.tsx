import React from 'react';

interface CTASectionProps {
  onButtonClick: (action: string) => void;
  onCTAKeyDown: (e: React.KeyboardEvent, buttonText: string) => void;
  isLoading: boolean;
  navigate: (path: string) => void;
}

const CTASection: React.FC<CTASectionProps> = ({
  onButtonClick,
  onCTAKeyDown,
  isLoading,
  navigate
}) => {
  return (
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
            onClick={() => {
              onButtonClick('Start Your Wealth Journey');
              navigate('/signup?source=cta');
            }}
            onKeyDown={(e) => onCTAKeyDown(e, 'Start Your Wealth Journey')}
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
            onClick={() => {
              onButtonClick('Join Our Community');
              navigate('/signup?source=cta');
            }}
            onKeyDown={(e) => onCTAKeyDown(e, 'Join Our Community')}
            disabled={isLoading}
            aria-label="Join our community of Black professionals"
            className="group border-2 border-white text-white hover:bg-white hover:text-violet-600 disabled:border-gray-400 disabled:text-gray-400 px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-white/25 hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-white focus-visible:ring-offset-4 focus-visible:ring-offset-violet-800"
          >
            {isLoading ? 'Loading...' : 'Join Our Community'}
          </button>
        </div>
      </div>
    </section>
  );
};

export default CTASection;

