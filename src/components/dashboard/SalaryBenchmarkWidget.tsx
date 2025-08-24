import React, { useState, useEffect } from 'react';
import { SalaryData, SalaryBenchmarkFilters } from '../../types/salary';

interface SalaryBenchmarkWidgetProps {
  userSalary?: number;
  onFiltersChange?: (filters: SalaryBenchmarkFilters) => void;
  className?: string;
}

const SalaryBenchmarkWidget: React.FC<SalaryBenchmarkWidgetProps> = ({
  userSalary = 75000,
  onFiltersChange,
  className = ''
}) => {
  const [salaryData, setSalaryData] = useState<SalaryData | null>(null);
  const [filters, setFilters] = useState<SalaryBenchmarkFilters>({
    msa: 'Atlanta-Sandy Springs-Alpharetta, GA',
    industry: 'Technology',
    experienceLevel: 'Mid-Level (3-7 years)',
    educationLevel: 'Bachelor\'s Degree',
    companySize: '500-1000 employees',
    role: 'Software Engineer'
  });
  const [isLoading, setIsLoading] = useState(true);
  const [showDrillDown, setShowDrillDown] = useState(false);

  // Mock data - replace with actual API call
  useEffect(() => {
    const fetchSalaryData = async () => {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockData: SalaryData = {
        userSalary,
        peerAverage: 82000,
        peerMedian: 78000,
        peer75thPercentile: 95000,
        peer25thPercentile: 65000,
        confidenceInterval: {
          lower: 76000,
          upper: 88000
        },
        sampleSize: 1247,
        msa: filters.msa,
        industry: filters.industry,
        experienceLevel: filters.experienceLevel,
        educationLevel: filters.educationLevel
      };
      
      setSalaryData(mockData);
      setIsLoading(false);
    };

    fetchSalaryData();
  }, [filters, userSalary]);

  const handleFilterChange = (key: keyof SalaryBenchmarkFilters, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  const getSalaryComparison = () => {
    if (!salaryData) return null;
    
    const difference = salaryData.userSalary - salaryData.peerMedian;
    const percentage = (difference / salaryData.peerMedian) * 100;
    
    return {
      difference,
      percentage,
      status: difference > 0 ? 'above' : difference < 0 ? 'below' : 'at'
    };
  };

  const comparison = getSalaryComparison();

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            Salary Benchmark
          </h3>
          <p className="text-sm text-gray-600">
            {filters.msa} • {filters.industry} • {filters.experienceLevel}
          </p>
        </div>
        <button
          onClick={() => setShowDrillDown(!showDrillDown)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          {showDrillDown ? 'Hide Details' : 'Drill Down'}
        </button>
      </div>

      {/* Main Comparison */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="text-2xl font-bold text-gray-900">
            ${userSalary.toLocaleString()}
          </div>
          <div className={`text-lg font-semibold ${
            comparison?.status === 'above' ? 'text-green-600' : 
            comparison?.status === 'below' ? 'text-red-600' : 'text-gray-600'
          }`}>
            {comparison?.status === 'above' ? '+' : ''}{comparison?.percentage.toFixed(1)}% vs median
          </div>
        </div>

        {/* Salary Range Visualization */}
        <div className="relative h-8 bg-gray-100 rounded-lg mb-4">
          <div className="absolute inset-0 flex items-center px-2">
            <div className="flex-1 relative">
              {/* 25th percentile */}
              <div 
                className="absolute h-4 bg-blue-300 rounded-l"
                style={{ 
                  left: '0%', 
                  width: '25%' 
                }}
              ></div>
              {/* Median */}
              <div 
                className="absolute h-4 bg-blue-500"
                style={{ 
                  left: '50%', 
                  width: '2px',
                  transform: 'translateX(-50%)'
                }}
              ></div>
              {/* 75th percentile */}
              <div 
                className="absolute h-4 bg-blue-300 rounded-r"
                style={{ 
                  left: '75%', 
                  width: '25%' 
                }}
              ></div>
              {/* User position */}
              <div 
                className={`absolute h-6 w-2 rounded-full ${
                  comparison?.status === 'above' ? 'bg-green-500' : 
                  comparison?.status === 'below' ? 'bg-red-500' : 'bg-gray-500'
                }`}
                style={{ 
                  left: `${Math.min(100, Math.max(0, ((userSalary - salaryData!.peer25thPercentile) / (salaryData!.peer75thPercentile - salaryData!.peer25thPercentile)) * 50 + 25))}%`,
                  transform: 'translateX(-50%)',
                  top: '-4px'
                }}
              ></div>
            </div>
          </div>
        </div>

        {/* Percentile labels */}
        <div className="flex justify-between text-xs text-gray-500 mb-4">
          <span>25th: ${salaryData?.peer25thPercentile.toLocaleString()}</span>
          <span>Median: ${salaryData?.peerMedian.toLocaleString()}</span>
          <span>75th: ${salaryData?.peer75thPercentile.toLocaleString()}</span>
        </div>
      </div>

      {/* Confidence and Sample Info */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">
            Confidence: {salaryData?.confidenceInterval.lower.toLocaleString()} - {salaryData?.confidenceInterval.upper.toLocaleString()}
          </span>
          <span className="text-gray-600">
            Sample: {salaryData?.sampleSize.toLocaleString()} professionals
          </span>
        </div>
      </div>

      {/* Drill Down Options */}
      {showDrillDown && (
        <div className="border-t pt-6">
          <h4 className="font-semibold text-gray-900 mb-4">Customize Comparison</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Metropolitan Area
              </label>
              <select
                value={filters.msa}
                onChange={(e) => handleFilterChange('msa', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Atlanta-Sandy Springs-Alpharetta, GA">Atlanta, GA</option>
                <option value="Washington-Arlington-Alexandria, DC-VA-MD-WV">Washington, DC</option>
                <option value="New York-Newark-Jersey City, NY-NJ-PA">New York, NY</option>
                <option value="Los Angeles-Long Beach-Anaheim, CA">Los Angeles, CA</option>
                <option value="Chicago-Naperville-Elgin, IL-IN-WI">Chicago, IL</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <select
                value={filters.industry}
                onChange={(e) => handleFilterChange('industry', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Technology">Technology</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Finance">Finance</option>
                <option value="Education">Education</option>
                <option value="Government">Government</option>
                <option value="Non-Profit">Non-Profit</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Experience Level
              </label>
              <select
                value={filters.experienceLevel}
                onChange={(e) => handleFilterChange('experienceLevel', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Entry-Level (0-2 years)">Entry-Level (0-2 years)</option>
                <option value="Mid-Level (3-7 years)">Mid-Level (3-7 years)</option>
                <option value="Senior (8-15 years)">Senior (8-15 years)</option>
                <option value="Executive (15+ years)">Executive (15+ years)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Size
              </label>
              <select
                value={filters.companySize}
                onChange={(e) => handleFilterChange('companySize', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1-50 employees">1-50 employees</option>
                <option value="51-200 employees">51-200 employees</option>
                <option value="201-500 employees">201-500 employees</option>
                <option value="500-1000 employees">500-1000 employees</option>
                <option value="1000+ employees">1000+ employees</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Current Salary
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-gray-500">$</span>
              <input
                type="number"
                value={userSalary}
                onChange={(e) => {
                  const newSalary = parseInt(e.target.value) || 0;
                  // This would typically update a parent component
                }}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your salary"
              />
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6">
        <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
          Get Detailed Report
        </button>
        <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors">
          Share Results
        </button>
      </div>
    </div>
  );
};

export default SalaryBenchmarkWidget; 