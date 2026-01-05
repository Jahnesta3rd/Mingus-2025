import React from 'react';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
}

interface FeaturesSectionProps {
  features: Feature[];
}

const FeaturesSection: React.FC<FeaturesSectionProps> = ({ features }) => {
  return (
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
  );
};

export default FeaturesSection;

