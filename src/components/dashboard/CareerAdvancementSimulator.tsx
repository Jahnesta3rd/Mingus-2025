import React, { useState, useEffect } from 'react';
import { CareerPath, CareerStep, CareerSimulatorParams } from '../../types/salary';

interface CareerAdvancementSimulatorProps {
  currentSalary?: number;
  targetSalary?: number;
  className?: string;
}

const CareerAdvancementSimulator: React.FC<CareerAdvancementSimulatorProps> = ({
  currentSalary = 75000,
  targetSalary = 100000,
  className = ''
}) => {
  const [params, setParams] = useState<CareerSimulatorParams>({
    currentEducation: 'Bachelor\'s Degree',
    targetEducation: 'Master\'s Degree',
    currentSkills: ['JavaScript', 'React', 'Node.js'],
    targetSkills: ['JavaScript', 'React', 'Node.js', 'Python', 'AWS', 'Leadership'],
    currentLocation: 'Atlanta, GA',
    targetLocation: 'Atlanta, GA',
    yearsOfExperience: 5,
    targetYearsOfExperience: 8,
    networkingScore: 6,
    targetNetworkingScore: 9
  });

  const [careerPath, setCareerPath] = useState<CareerPath | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Mock career path calculation
  useEffect(() => {
    const calculateCareerPath = async () => {
      setIsCalculating(true);
      await new Promise(resolve => setTimeout(resolve, 800));

      const educationStep: CareerStep = {
        id: 'education',
        title: 'Pursue Advanced Degree',
        description: 'Complete Master\'s in Computer Science or MBA',
        cost: 45000,
        duration: 24,
        salaryIncrease: 15000,
        type: 'education',
        priority: 'high'
      };

      const certificationStep: CareerStep = {
        id: 'certification',
        title: 'Obtain Professional Certifications',
        description: 'AWS Solutions Architect, PMP, or relevant industry certs',
        cost: 5000,
        duration: 6,
        salaryIncrease: 8000,
        type: 'certification',
        priority: 'medium'
      };

      const skillStep: CareerStep = {
        id: 'skills',
        title: 'Develop Leadership Skills',
        description: 'Take on team lead responsibilities and management training',
        cost: 3000,
        duration: 12,
        salaryIncrease: 12000,
        type: 'skill',
        priority: 'high'
      };

      const networkingStep: CareerStep = {
        id: 'networking',
        title: 'Build Professional Network',
        description: 'Join industry groups, attend conferences, mentor others',
        cost: 2000,
        duration: 18,
        salaryIncrease: 5000,
        type: 'networking',
        priority: 'medium'
      };

      const totalInvestment = educationStep.cost + certificationStep.cost + skillStep.cost + networkingStep.cost;
      const totalSalaryIncrease = educationStep.salaryIncrease + certificationStep.cost + skillStep.salaryIncrease + networkingStep.salaryIncrease;
      const roi = ((totalSalaryIncrease * 5) - totalInvestment) / totalInvestment * 100; // 5 years of increased salary

      const mockCareerPath: CareerPath = {
        currentSalary,
        targetSalary: currentSalary + totalSalaryIncrease,
        yearsToTarget: 2,
        steps: [educationStep, certificationStep, skillStep, networkingStep],
        totalInvestment,
        roi
      };

      setCareerPath(mockCareerPath);
      setIsCalculating(false);
    };

    calculateCareerPath();
  }, [params, currentSalary]);

  const handleParamChange = (key: keyof CareerSimulatorParams, value: any) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const getProgressPercentage = () => {
    if (!careerPath) return 0;
    return Math.min(100, (currentSalary / targetSalary) * 100);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2" className="text-xl font-semibold text-gray-800 mb-3">
          Career Advancement Simulator
        </h3>
        <p className="text-base leading-relaxed text-gray-600">
          Explore your path to higher earnings through strategic career development
        </p>
      </div>

      {/* Path to $100K Visualization */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-semibold text-gray-900">Path to $100K</h4>
          <div className="text-base leading-relaxed text-gray-600">
            {formatCurrency(currentSalary)} → {formatCurrency(targetSalary)}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative h-4 bg-gray-200 rounded-full mb-4">
          <div 
            className="absolute h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-base leading-relaxed font-medium text-white drop-shadow">
              {getProgressPercentage().toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Milestone Markers */}
        <div className="flex justify-between text-base leading-relaxed text-gray-500">
          <span>Current: {formatCurrency(currentSalary)}</span>
          <span>Target: {formatCurrency(targetSalary)}</span>
        </div>
      </div>

      {/* Interactive Sliders */}
      <div className="space-y-6 mb-8">
        {/* Education Level */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-base leading-relaxed font-medium text-gray-700">Education Level</label>
            <span className="text-base leading-relaxed text-gray-600">{params.targetEducation}</span>
          </div>
          <select
            value={params.targetEducation}
            onChange={(e) => handleParamChange('targetEducation', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="High School">High School</option>
            <option value="Associate's Degree">Associate's Degree</option>
            <option value="Bachelor's Degree">Bachelor's Degree</option>
            <option value="Master's Degree">Master's Degree</option>
            <option value="Doctorate">Doctorate</option>
          </select>
        </div>

        {/* Years of Experience */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-base leading-relaxed font-medium text-gray-700">Target Experience (Years)</label>
            <span className="text-base leading-relaxed text-gray-600">{params.targetYearsOfExperience} years</span>
          </div>
          <input
            type="range"
            min="1"
            max="20"
            value={params.targetYearsOfExperience}
            onChange={(e) => handleParamChange('targetYearsOfExperience', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-base leading-relaxed text-gray-500 mt-1">
            <span>1 year</span>
            <span>20 years</span>
          </div>
        </div>

        {/* Networking Score */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-base leading-relaxed font-medium text-gray-700">Networking Score</label>
            <span className="text-base leading-relaxed text-gray-600">{params.targetNetworkingScore}/10</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            value={params.targetNetworkingScore}
            onChange={(e) => handleParamChange('targetNetworkingScore', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-base leading-relaxed text-gray-500 mt-1">
            <span>Beginner</span>
            <span>Expert</span>
          </div>
        </div>

        {/* Location */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-base leading-relaxed font-medium text-gray-700">Target Location</label>
            <span className="text-base leading-relaxed text-gray-600">{params.targetLocation}</span>
          </div>
          <select
            value={params.targetLocation}
            onChange={(e) => handleParamChange('targetLocation', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Atlanta, GA">Atlanta, GA</option>
            <option value="Washington, DC">Washington, DC</option>
            <option value="New York, NY">New York, NY</option>
            <option value="Los Angeles, CA">Los Angeles, CA</option>
            <option value="Chicago, IL">Chicago, IL</option>
            <option value="Remote">Remote</option>
          </select>
        </div>
      </div>

      {/* Career Path Results */}
      {isCalculating ? (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      ) : careerPath && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(careerPath.targetSalary)}
                </div>
                <div className="text-base leading-relaxed text-gray-600">Projected Salary</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {careerPath.roi.toFixed(0)}%
                </div>
                <div className="text-base leading-relaxed text-gray-600">ROI</div>
              </div>
            </div>
          </div>

          {/* Career Steps */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Recommended Steps</h4>
            <div className="space-y-3">
              {careerPath.steps.map((step, index) => (
                <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h5 className="font-medium text-gray-900">{step.title}</h5>
                      <p className="text-base leading-relaxed text-gray-600">{step.description}</p>
                    </div>
                    <span className={`px-2 py-1 text-base leading-relaxed rounded-full ${
                      step.priority === 'high' ? 'bg-red-100 text-red-800' :
                      step.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {step.priority}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-base leading-relaxed">
                    <div>
                      <span className="text-gray-500">Cost:</span>
                      <div className="font-medium">{formatCurrency(step.cost)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <div className="font-medium">{step.duration} months</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Salary Increase:</span>
                      <div className="font-medium text-green-600">+{formatCurrency(step.salaryIncrease)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Investment Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-3">Investment Summary</h5>
            <div className="space-y-2 text-base leading-relaxed">
              <div className="flex justify-between">
                <span>Total Investment:</span>
                <span className="font-medium">{formatCurrency(careerPath.totalInvestment)}</span>
              </div>
              <div className="flex justify-between">
                <span>Time to Target:</span>
                <span className="font-medium">{careerPath.yearsToTarget} years</span>
              </div>
              <div className="flex justify-between">
                <span>Annual Salary Increase:</span>
                <span className="font-medium text-green-600">
                  +{formatCurrency(careerPath.steps.reduce((sum, step) => sum + step.salaryIncrease, 0))}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6">
        <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
          Save Career Plan
        </button>
        <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors">
          Get Mentorship
        </button>
      </div>
    </div>
  );
};

export default CareerAdvancementSimulator; 