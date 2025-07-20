import React from 'react';

interface GoalTypeCardProps {
  icon: string;
  name: string;
  description: string;
  examples: string[];
  selected: boolean;
  onClick: () => void;
}

const GoalTypeCard: React.FC<GoalTypeCardProps> = ({
  icon,
  name,
  description,
  examples,
  selected,
  onClick
}) => {
  return (
    <div
      onClick={onClick}
      className={`relative p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 hover:shadow-lg ${
        selected
          ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      {/* Selection Indicator */}
      {selected && (
        <div className="absolute top-4 right-4 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}

      {/* Icon */}
      <div className="text-4xl mb-4">{icon}</div>

      {/* Title */}
      <h3 className={`text-lg font-semibold mb-2 ${
        selected ? 'text-blue-900' : 'text-gray-900'
      }`}>
        {name}
      </h3>

      {/* Description */}
      <p className={`text-sm mb-4 ${
        selected ? 'text-blue-700' : 'text-gray-600'
      }`}>
        {description}
      </p>

      {/* Examples */}
      <div className="space-y-1">
        {examples.map((example, index) => (
          <div
            key={index}
            className={`text-xs px-2 py-1 rounded-full ${
              selected
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {example}
          </div>
        ))}
      </div>

      {/* Hover Effect */}
      <div className={`absolute inset-0 rounded-2xl transition-opacity duration-300 ${
        selected
          ? 'bg-gradient-to-br from-blue-500/5 to-indigo-500/5'
          : 'bg-gradient-to-br from-gray-500/0 to-gray-500/0 hover:from-gray-500/5 hover:to-gray-500/5'
      }`} />
    </div>
  );
};

export default GoalTypeCard; 