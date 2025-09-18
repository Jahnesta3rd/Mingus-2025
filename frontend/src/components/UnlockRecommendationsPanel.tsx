import React from 'react';
import { 
  Lock, 
  Target, 
  TrendingUp, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  ArrowRight
} from 'lucide-react';

interface UnlockRecommendationsPanelProps {
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
}

const UnlockRecommendationsPanel: React.FC<UnlockRecommendationsPanelProps> = ({ 
  riskLevel 
}) => {
  const getRiskConfig = (level: string) => {
    const configs = {
      secure: {
        color: 'green',
        icon: Shield,
        title: 'Unlock Job Recommendations',
        description: 'Complete your career assessment to access personalized job recommendations tailored to your profile and goals.',
        urgency: 'low',
        benefits: [
          'Personalized job matches based on your skills',
          'Salary increase potential analysis',
          'Career advancement opportunities',
          'Industry-specific recommendations'
        ]
      },
      watchful: {
        color: 'yellow',
        icon: AlertTriangle,
        title: 'Strategic Job Recommendations',
        description: 'Market changes detected. Unlock strategic job recommendations to stay ahead of industry trends.',
        urgency: 'medium',
        benefits: [
          'Strategic positioning recommendations',
          'Market trend analysis',
          'Competitive salary insights',
          'Growth opportunity identification'
        ]
      },
      action_needed: {
        color: 'orange',
        icon: Target,
        title: 'Protection Job Recommendations',
        description: 'Career risk identified. Access protection-focused job recommendations to secure your professional future.',
        urgency: 'high',
        benefits: [
          'Risk-mitigation job opportunities',
          'Stable career path options',
          'Emergency job recommendations',
          'Protection-focused strategies'
        ]
      },
      urgent: {
        color: 'red',
        icon: AlertTriangle,
        title: 'Emergency Job Recommendations',
        description: 'High risk detected. Immediate access to emergency job recommendations to protect your career.',
        urgency: 'critical',
        benefits: [
          'Immediate job opportunities',
          'Emergency career protection',
          'Rapid application strategies',
          'Crisis management support'
        ]
      }
    };
    
    return configs[level as keyof typeof configs] || configs.secure;
  };

  const config = getRiskConfig(riskLevel);
  const IconComponent = config.icon;

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleUnlockClick = () => {
    // Track unlock attempt
    trackAnalyticsEvent('recommendations_unlock_attempted', {
      risk_level: riskLevel,
      urgency: config.urgency
    });

    // Navigate to assessment or unlock flow
    if (riskLevel === 'urgent') {
      // Emergency unlock - immediate access
      window.location.href = '/emergency-unlock';
    } else {
      // Regular assessment flow
      window.location.href = '/assessment';
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className={`bg-gradient-to-br from-${config.color}-50 to-${config.color}-100 border border-${config.color}-200 rounded-2xl p-8`}>
        {/* Header */}
        <div className="text-center mb-8">
          <div className={`inline-flex items-center justify-center w-16 h-16 bg-${config.color}-100 rounded-full mb-4`}>
            <IconComponent className={`h-8 w-8 text-${config.color}-600`} />
          </div>
          
          <h2 className={`text-3xl font-bold text-${config.color}-900 mb-4`}>
            {config.title}
          </h2>
          
          <p className={`text-lg text-${config.color}-700 mb-6 max-w-2xl mx-auto`}>
            {config.description}
          </p>

          {/* Urgency Badge */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold ${getUrgencyColor(config.urgency)}`}>
            {config.urgency === 'critical' && <AlertTriangle className="h-4 w-4" />}
            {config.urgency === 'high' && <Target className="h-4 w-4" />}
            {config.urgency === 'medium' && <TrendingUp className="h-4 w-4" />}
            {config.urgency === 'low' && <Shield className="h-4 w-4" />}
            {config.urgency.toUpperCase()} PRIORITY
          </div>
        </div>

        {/* Benefits Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {config.benefits.map((benefit, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className={`flex-shrink-0 w-6 h-6 bg-${config.color}-200 rounded-full flex items-center justify-center mt-0.5`}>
                <CheckCircle className={`h-4 w-4 text-${config.color}-600`} />
              </div>
              <p className={`text-${config.color}-800 font-medium`}>
                {benefit}
              </p>
            </div>
          ))}
        </div>

        {/* Unlock Button */}
        <div className="text-center">
          <button
            onClick={handleUnlockClick}
            className={`
              inline-flex items-center gap-3 bg-${config.color}-600 hover:bg-${config.color}-700 
              text-white font-semibold py-4 px-8 rounded-xl transition-all duration-200 
              transform hover:scale-105 hover:shadow-lg
            `}
          >
            {riskLevel === 'urgent' ? (
              <>
                <AlertTriangle className="h-5 w-5" />
                Emergency Unlock Now
              </>
            ) : (
              <>
                <Lock className="h-5 w-5" />
                Unlock Recommendations
              </>
            )}
            <ArrowRight className="h-5 w-5" />
          </button>
          
          <p className={`text-sm text-${config.color}-600 mt-4`}>
            {riskLevel === 'urgent' 
              ? 'Immediate access granted due to high career risk'
              : 'Complete a quick assessment to unlock personalized recommendations'
            }
          </p>
        </div>
      </div>

      {/* Additional Information */}
      <div className="mt-8 grid md:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <Target className="h-8 w-8 text-blue-600 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Personalized Matching</h3>
          <p className="text-gray-600 text-sm">
            AI-powered job matching based on your skills, experience, and career goals.
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <TrendingUp className="h-8 w-8 text-green-600 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Salary Insights</h3>
          <p className="text-gray-600 text-sm">
            Detailed salary analysis and increase potential for each opportunity.
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <Shield className="h-8 w-8 text-purple-600 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Career Protection</h3>
          <p className="text-gray-600 text-sm">
            Strategic recommendations to protect and advance your career.
          </p>
        </div>
      </div>
    </div>
  );
};

// Helper Functions
const trackAnalyticsEvent = (eventType: string, eventData: any) => {
  try {
    const sessionId = getSessionId();
    const userId = getCurrentUserId();
    
    fetch('/api/analytics/user-behavior/track-interaction', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCSRFToken()
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_id: userId,
        interaction_type: eventType,
        page_url: window.location.pathname,
        element_id: 'unlock-recommendations-panel',
        element_text: 'Unlock Recommendations Panel',
        interaction_data: eventData
      })
    });
  } catch (error) {
    console.error('Failed to track analytics event:', error);
  }
};

const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('mingus_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('mingus_session_id', sessionId);
  }
  return sessionId;
};

const getCurrentUserId = (): string => {
  return localStorage.getItem('mingus_user_id') || 'anonymous';
};

const getCSRFToken = (): string => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content') || '';
  }
  
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return value;
    }
  }
  
  return '';
};

export default UnlockRecommendationsPanel;
