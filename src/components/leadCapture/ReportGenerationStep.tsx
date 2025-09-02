import React from 'react';
import { PersonalizedReport, BasicLeadInfo, DetailedProfile } from '../../types/leadCapture';

interface ReportGenerationStepProps {
  onGenerateReport: () => void;
  onBack: () => void;
  isGenerating: boolean;
  report?: PersonalizedReport | null;
  basicInfo: BasicLeadInfo;
  detailedProfile: DetailedProfile;
}

const ReportGenerationStep: React.FC<ReportGenerationStepProps> = ({
  onGenerateReport,
  onBack,
  isGenerating,
  report,
  basicInfo,
  detailedProfile
}) => {
  if (isGenerating) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4" className="text-2xl font-semibold text-gray-800 mb-4">
            Generating Your Personalized Report
          </h2>
          <p className="text-lg text-gray-600">
            Analyzing your profile and creating detailed insights...
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-6"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4" className="text-xl font-semibold text-gray-800 mb-3">
            Processing Your Data
          </h3>
          <div className="space-y-3 text-left max-w-md mx-auto">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">Analyzing salary benchmarks</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">Calculating career projections</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-gray-600">Generating skill recommendations</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
              <span className="text-gray-400">Preparing market insights</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (report) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4" className="text-2xl font-semibold text-gray-800 mb-4">
            Your Personalized Career Report
          </h2>
          <p className="text-lg text-gray-600">
            Generated on {report.generatedAt.toLocaleDateString()}
          </p>
        </div>

        {/* Report Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-blue-50 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              ${report.salaryProjections[4]?.projectedSalary.toLocaleString()}
            </div>
            <div className="text-base leading-relaxed text-blue-700">5-Year Projected Salary</div>
          </div>
          <div className="bg-green-50 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {report.skillRecommendations.length}
            </div>
            <div className="text-base leading-relaxed text-green-700">Skills to Develop</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {report.careerPathRecommendations.length}
            </div>
            <div className="text-base leading-relaxed text-purple-700">Career Paths Available</div>
          </div>
        </div>

        {/* Salary Projections */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4" className="text-xl font-semibold text-gray-800 mb-3">5-Year Salary Projections</h3>
          <div className="space-y-4">
            {report.salaryProjections.map((projection) => (
              <div key={projection.year} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-semibold text-gray-900">Year {projection.year}</div>
                  <div className="text-base leading-relaxed text-gray-600">
                    {projection.factors.join(', ')}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">
                    ${projection.projectedSalary.toLocaleString()}
                  </div>
                  <div className="text-base leading-relaxed text-green-600">
                    +{projection.growthRate.toFixed(1)}% growth
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Skill Recommendations */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4" className="text-xl font-semibold text-gray-800 mb-3">Skill Development Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.skillRecommendations.map((skill) => (
              <div key={skill.skill} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-gray-900">{skill.skill}</h4>
                  <span className={`px-2 py-1 text-base leading-relaxed rounded-full ${
                    skill.priority === 'high' ? 'bg-red-100 text-red-800' :
                    skill.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {skill.priority}
                  </span>
                </div>
                <p className="text-base leading-relaxed text-gray-600 mb-3">{skill.learningPath}</p>
                <div className="flex justify-between text-base leading-relaxed">
                  <span className="text-gray-500">Impact: +${skill.impact.toLocaleString()}</span>
                  <span className="text-gray-500">Cost: ${skill.cost.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mingus Platform Preview */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white mb-6">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold mb-2" className="text-xl font-semibold text-gray-800 mb-3">Unlock Your Full Potential</h3>
            <p className="text-blue-100">
              Get access to advanced features and personalized coaching
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {report.mingusPlatformPreview.pricing.map((tier) => (
              <div key={tier.name} className={`bg-white rounded-lg p-6 text-gray-900 ${
                tier.popular ? 'ring-2 ring-yellow-400' : ''
              }`}>
                {tier.popular && (
                  <div className="bg-yellow-400 text-yellow-900 text-base leading-relaxed font-bold px-2 py-1 rounded-full text-center mb-3">
                    MOST POPULAR
                  </div>
                )}
                <h4 className="text-lg font-semibold mb-2">{tier.name}</h4>
                <div className="text-3xl font-bold mb-4">
                  ${tier.price}<span className="text-base leading-relaxed font-normal">/{tier.period}</span>
                </div>
                <ul className="space-y-2 text-base leading-relaxed">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="text-center">
            <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
              {report.mingusPlatformPreview.ctaText}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={onBack}
            className="flex-1 bg-gray-100 text-gray-700 py-4 px-6 rounded-lg font-semibold text-lg hover:bg-gray-200 transition-all duration-200"
          >
            Back to Profile
          </button>
          <button
            onClick={() => window.print()}
            className="flex-1 bg-blue-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-all duration-200"
          >
            Download PDF
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4" className="text-2xl font-semibold text-gray-800 mb-4">
          Ready to Generate Your Report?
        </h2>
        <p className="text-lg text-gray-600">
          Based on your profile, we'll create a personalized 5-year career plan with salary projections and skill recommendations.
        </p>
      </div>

      {/* Profile Summary */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-4" className="text-xl font-semibold text-gray-800 mb-3">Your Profile Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Basic Information</h4>
            <div className="space-y-2 text-base leading-relaxed">
              <div><span className="text-gray-500">Current Salary:</span> ${basicInfo.currentSalary.toLocaleString()}</div>
              <div><span className="text-gray-500">Location:</span> {basicInfo.location}</div>
              <div><span className="text-gray-500">Industry:</span> {detailedProfile.industry}</div>
              <div><span className="text-gray-500">Role:</span> {detailedProfile.role}</div>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Career Goals</h4>
            <div className="space-y-2 text-base leading-relaxed">
              <div><span className="text-gray-500">Target Salary:</span> ${detailedProfile.targetSalary.toLocaleString()}</div>
              <div><span className="text-gray-500">Experience:</span> {detailedProfile.yearsOfExperience} years</div>
              <div><span className="text-gray-500">Education:</span> {detailedProfile.education}</div>
              <div><span className="text-gray-500">Goals:</span> {detailedProfile.careerGoals.length} selected</div>
            </div>
          </div>
        </div>
      </div>

      {/* What You'll Get */}
      <div className="bg-blue-50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-blue-900 mb-4" className="text-xl font-semibold text-gray-800 mb-3">What's Included in Your Report:</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-base leading-relaxed">1</div>
            <span className="text-blue-800">5-year salary projections with growth factors</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-base leading-relaxed">2</div>
            <span className="text-blue-800">Personalized skill development recommendations</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-base leading-relaxed">3</div>
            <span className="text-blue-800">Career path analysis with ROI calculations</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-base leading-relaxed">4</div>
            <span className="text-blue-800">Market insights and industry trends</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-base leading-relaxed">5</div>
            <span className="text-blue-800">Mingus platform preview and exclusive offers</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex-1 bg-gray-100 text-gray-700 py-4 px-6 rounded-lg font-semibold text-lg hover:bg-gray-200 transition-all duration-200"
        >
          Back
        </button>
        <button
          onClick={onGenerateReport}
          className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
        >
          Generate My Report
        </button>
      </div>
    </div>
  );
};

export default ReportGenerationStep; 