import React from 'react';
import { Check } from 'lucide-react';

interface PricingTier {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  popular?: boolean;
  cta: string;
}

interface PricingSectionProps {
  pricingTiers: PricingTier[];
  navigate: (path: string) => void;
}

const PricingSection: React.FC<PricingSectionProps> = ({ pricingTiers, navigate }) => {
  return (
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
              <ul className="space-y-3 mb-8" id={`${tier.name.toLowerCase().replace(/\s+/g, '-')}-features`}>
                {tier.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start group-hover:translate-x-1 transition-transform duration-300" style={{transitionDelay: `${featureIndex * 50}ms`}}>
                    <Check className="w-5 h-5 text-violet-400 mt-0.5 mr-3 flex-shrink-0 group-hover:text-violet-300 transition-colors duration-300" aria-hidden="true" />
                    <span className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{feature}</span>
                  </li>
                ))}
              </ul>
              <div id={`${tier.name.toLowerCase().replace(/\s+/g, '-')}-description`} className="sr-only">
                {tier.description}. Features include: {tier.features.join(', ')}
              </div>
              <button 
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                  tier.popular 
                    ? 'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white shadow-lg hover:shadow-violet-500/25' 
                    : 'border-2 border-violet-500 text-violet-400 hover:bg-violet-500 hover:text-white hover:shadow-lg hover:shadow-violet-500/25'
                }`}
                aria-label={`Subscribe to ${tier.name} plan for ${tier.price} per ${tier.period}`}
                aria-describedby={`${tier.name.toLowerCase().replace(/\s+/g, '-')}-description ${tier.name.toLowerCase().replace(/\s+/g, '-')}-features`}
                onClick={() => navigate('/signup')}
              >
                {tier.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PricingSection;

