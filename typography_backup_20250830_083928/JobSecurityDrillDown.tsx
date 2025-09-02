import React from 'react';
import { 
  X, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  MapPin,
  Building,
  Users,
  DollarSign,
  Calendar,
  BarChart3
} from 'lucide-react';

interface DrillDownData {
  component: 'user_perception' | 'external_data';
  details: {
    factors: FactorDetail[];
    trends: TrendDetail[];
    insights: string[];
    recommendations: string[];
  };
}

interface FactorDetail {
  name: string;
  value: number;
  weight: number;
  trend: 'up' | 'down' | 'stable';
  description: string;
}

interface TrendDetail {
  period: string;
  value: number;
  change: number;
  significance: 'high' | 'medium' | 'low';
}

interface JobSecurityDrillDownProps {
  data: DrillDownData;
  onClose: () => void;
  className?: string;
}

const JobSecurityDrillDown: React.FC<JobSecurityDrillDownProps> = ({
  data,
  onClose,
  className = ''
}) => {
  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <div className="w-4 h-4 border-t-2 border-gray-400" />;
    }
  };

  const getSignificanceColor = (significance: 'high' | 'medium' | 'low') => {
    switch (significance) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const getComponentIcon = () => {
    return data.component === 'user_perception' ? (
      <Users className="w-6 h-6 text-blue-600" />
    ) : (
      <Building className="w-6 h-6 text-green-600" />
    );
  };

  const getComponentTitle = () => {
    return data.component === 'user_perception' 
      ? 'User Perception Analysis' 
      : 'External Data Analysis';
  };

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 ${className}`}>
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              {getComponentIcon()}
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">{getComponentTitle()}</h3>
              <p className="text-sm text-gray-500">
                Detailed breakdown of {data.component === 'user_perception' ? 'your workplace perceptions' : 'external market factors'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Contributing Factors */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
              Contributing Factors
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.details.factors.map((factor, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">{factor.name}</span>
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(factor.trend)}
                      <span className="text-sm font-semibold text-gray-700">
                        {factor.value}
                      </span>
                    </div>
                  </div>
                  <div className="mb-2">
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                      <span>Weight: {factor.weight}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${factor.weight}%` }}
                      />
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{factor.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Trends */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="w-5 h-5 text-green-600 mr-2" />
              Recent Trends
            </h4>
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Period
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Value
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Change
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Significance
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.details.trends.map((trend, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {trend.period}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {trend.value}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`font-medium ${
                            trend.change > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trend.change > 0 ? '+' : ''}{trend.change}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignificanceColor(trend.significance)}`}>
                            {trend.significance.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Key Insights */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              Key Insights
            </h4>
            <div className="space-y-3">
              {data.details.insights.map((insight, index) => (
                <div key={index} className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-green-800">{insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
              Recommendations
            </h4>
            <div className="space-y-3">
              {data.details.recommendations.map((rec, index) => (
                <div key={index} className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-yellow-800">{rec}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default JobSecurityDrillDown; 