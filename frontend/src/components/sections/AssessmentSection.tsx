import React from 'react';
import { Heart, TrendingUp, Calendar, Target, Car } from 'lucide-react';
import { AssessmentType } from '../../types/assessments';

interface AssessmentSectionProps {
  onAssessmentClick: (assessmentType: AssessmentType) => void;
  onAssessmentKeyDown: (e: React.KeyboardEvent, assessmentType: AssessmentType) => void;
  isLoading: boolean;
}

const AssessmentSection: React.FC<AssessmentSectionProps> = ({
  onAssessmentClick,
  onAssessmentKeyDown,
  isLoading
}) => {
  return (
    <section aria-labelledby="assessments-heading" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900" role="region">
      <div className="max-w-7xl mx-auto">
        <h2 id="assessments-heading" className="text-3xl md:text-4xl font-bold mb-4 text-center">
          Choose Your Assessment
        </h2>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto text-center mb-12">
          Take our specialized assessments to understand your financial position and opportunities for growth.
        </p>
        
        {/* Assessment Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6" role="list" aria-label="Assessment options">
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
              onClick={() => onAssessmentClick('ai-risk')}
              onKeyDown={(e) => onAssessmentKeyDown(e, 'ai-risk')}
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
              onClick={() => onAssessmentClick('income-comparison')}
              onKeyDown={(e) => onAssessmentKeyDown(e, 'income-comparison')}
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
              onClick={() => onAssessmentClick('cuffing-season')}
              onKeyDown={(e) => onAssessmentKeyDown(e, 'cuffing-season')}
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
              onClick={() => onAssessmentClick('layoff-risk')}
              onKeyDown={(e) => onAssessmentKeyDown(e, 'layoff-risk')}
              disabled={isLoading}
              aria-label="Take Layoff Risk Assessment"
              className="w-full bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-700 hover:to-red-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-rose-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-rose-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
              type="button"
            >
              {isLoading ? 'Loading...' : 'Take Assessment'}
            </button>
          </div>

          {/* Vehicle Financial Health Card */}
          <div className="group bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-emerald-500 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-emerald-500/20 hover:-translate-y-2" role="listitem">
            <div className="text-emerald-400 mb-4 group-hover:text-emerald-300 transition-all duration-300 transform group-hover:scale-110" aria-hidden="true">
              <Car className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-semibold mb-3 text-white group-hover:text-emerald-100 transition-colors duration-300">
              Vehicle Financial Health
            </h3>
            <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300 leading-relaxed mb-4">
              Evaluate your vehicle-related financial wellness and planning strategies.
            </p>
            <button 
              onClick={() => onAssessmentClick('vehicle-financial-health')}
              onKeyDown={(e) => onAssessmentKeyDown(e, 'vehicle-financial-health')}
              disabled={isLoading}
              aria-label="Take Vehicle Financial Health Assessment"
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-emerald-500/25 flex items-center justify-center hover:-translate-y-1 disabled:scale-100 disabled:translate-y-0 disabled:cursor-not-allowed focus-ring focus-visible:ring-4 focus-visible:ring-emerald-400 focus-visible:ring-offset-4 focus-visible:ring-offset-gray-900"
              type="button"
            >
              {isLoading ? 'Loading...' : 'Take Assessment'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AssessmentSection;

