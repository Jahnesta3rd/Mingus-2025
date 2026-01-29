import React, { useState, useEffect } from 'react';
import { AlertTriangle, Shield, TrendingUp, Zap } from 'lucide-react';

interface RiskData {
  overall_risk: number;
  risk_level: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  primary_threats: Array<{
    factor: string;
    urgency: string;
    timeline: string;
  }>;
  recommendations_available: boolean;
  emergency_unlock_granted: boolean;
}

interface RiskStatusHeroProps {
  className?: string;
  onRiskLevelChange?: (riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent') => void;
}

const RiskStatusHero: React.FC<RiskStatusHeroProps> = ({ className = '', onRiskLevelChange }) => {
  const [riskData, setRiskData] = useState<RiskData | null>({
    overall_risk: 0,
    risk_level: 'watchful',
    primary_threats: [],
    recommendations_available: false,
    emergency_unlock_granted: false
  });
  const [loading, setLoading] = useState(true);
  const [animateRing, setAnimateRing] = useState(false);
  
  useEffect(() => {
    fetchRiskStatus();
  }, []);
  
  const fetchRiskStatus = async () => {
    try {
      const response = await fetch('/api/risk/assess-and-track', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({ user_profile: getCurrentUserProfile() })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const riskAnalysis = data.risk_analysis || {};
      setRiskData({
        overall_risk: riskAnalysis.overall_risk ?? riskAnalysis.score ?? 0,
        risk_level: riskAnalysis.risk_level || 'watchful',
        primary_threats: riskAnalysis.primary_threats || riskAnalysis.factors || [],
        recommendations_available: riskAnalysis.recommendations_available ?? false,
        emergency_unlock_granted: riskAnalysis.emergency_unlock_granted ?? false
      });
      setAnimateRing(true);
      
      // Notify parent component of risk level change
      if (onRiskLevelChange) {
        onRiskLevelChange(riskAnalysis.risk_level || 'watchful');
      }
      
      // Track analytics for hero component interaction
      await trackAnalyticsEvent('risk_hero_viewed', {
        risk_level: riskAnalysis.risk_level || 'watchful',
        risk_score: riskAnalysis.overall_risk ?? riskAnalysis.score ?? 0
      });
      
    } catch (error) {
      console.error('Failed to fetch risk status:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const getRiskConfig = (riskLevel: string, riskScore: number) => {
    const configs = {
      secure: {
        gradient: 'from-emerald-500 to-emerald-600',
        icon: Shield,
        message: 'Career on track - stay prepared',
        cta: 'Explore growth opportunities',
        ringColor: '#10b981'
      },
      watchful: {
        gradient: 'from-amber-500 to-amber-600', 
        icon: TrendingUp,
        message: 'Market changes detected - strategic positioning recommended',
        cta: 'View strategic recommendations',
        ringColor: '#f59e0b'
      },
      action_needed: {
        gradient: 'from-orange-500 to-orange-600',
        icon: AlertTriangle,
        message: 'Career risk identified - proactive steps recommended', 
        cta: 'See protection plan',
        ringColor: '#f97316'
      },
      urgent: {
        gradient: 'from-red-500 to-red-600',
        icon: Zap,
        message: 'High risk detected - immediate action required',
        cta: 'Get emergency recommendations',
        ringColor: '#dc2626'
      }
    };
    
    return configs[riskLevel as keyof typeof configs] || configs.secure;
  };
  
  const handleCTAClick = async () => {
    if (!riskData) return;
    
    // Track CTA interaction
    await trackAnalyticsEvent('risk_hero_cta_clicked', {
      risk_level: riskData.risk_level,
      cta_text: getRiskConfig(riskData.risk_level, riskData.overall_risk).cta
    });
    
    // Navigate based on risk level
    if (riskData.risk_level === 'urgent' && riskData.emergency_unlock_granted) {
      window.location.href = '/emergency-job-recommendations';
    } else if (riskData.recommendations_available) {
      window.location.href = '/job-recommendations';
    } else {
      window.location.href = '/referral-progress';
    }
  };
  
  if (loading) {
    return <RiskHeroSkeleton />;
  }
  
  if (!riskData) {
    return <RiskHeroError onRetry={fetchRiskStatus} />;
  }
  
  const config = getRiskConfig(riskData.risk_level || 'watchful', riskData.overall_risk || 0);
  const IconComponent = config.icon;
  
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${config.gradient} p-6 text-white shadow-xl ${className}`}>
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" />
      
      {/* Content Container */}
      <div className="relative z-10 flex items-center justify-between">
        {/* Left Side - Risk Information */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <IconComponent className="h-8 w-8" />
            <div>
              <h2 className="text-lg font-semibold capitalize">{(riskData?.risk_level || 'watchful').replace('_', ' ')} Status</h2>
              <p className="text-sm text-white/80">Career Risk Assessment</p>
            </div>
          </div>
          
          <p className="text-base mb-4 leading-relaxed">
            {config.message}
          </p>
          
          {/* Primary Threat Preview */}
          {(riskData?.primary_threats?.length ?? 0) > 0 && (
            <div className="mb-4">
              <p className="text-sm text-white/90 font-medium">
                Primary Risk: {riskData?.primary_threats?.[0]?.factor ?? 'N/A'}
              </p>
              <p className="text-xs text-white/70">
                Timeline: {riskData?.primary_threats?.[0]?.timeline ?? 'N/A'}
              </p>
            </div>
          )}
          
          {/* CTA Button */}
          <button
            onClick={handleCTAClick}
            className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 rounded-lg px-6 py-3 text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/50"
            aria-label={`${config.cta} - Risk level: ${riskData?.risk_level || 'watchful'}`}
          >
            {config.cta}
          </button>
        </div>
        
        {/* Right Side - Risk Score Ring */}
        <div className="flex-shrink-0 ml-6">
          <RiskScoreRing
            score={Math.round(riskData.overall_risk * 100)}
            color={config.ringColor}
            animate={animateRing}
          />
        </div>
      </div>
      
      {/* Emergency Indicator */}
      {(riskData?.risk_level || 'watchful') === 'urgent' && (
        <div className="absolute top-2 right-2">
          <div className="bg-white/20 rounded-full p-2 animate-pulse" aria-label="Emergency alert">
            <Zap className="h-4 w-4" />
          </div>
        </div>
      )}
    </div>
  );
};

// Risk Score Ring Component
const RiskScoreRing: React.FC<{
  score: number;
  color: string;
  animate: boolean;
}> = ({ score, color, animate }) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  return (
    <div className="relative w-24 h-24">
      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100" aria-label={`Risk score: ${score}%`}>
        {/* Background Circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke="rgba(255,255,255,0.2)"
          strokeWidth="8"
          fill="transparent"
        />
        {/* Progress Circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke={color}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={animate ? strokeDashoffset : circumference}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      
      {/* Score Text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl font-bold">{score}</div>
          <div className="text-xs text-white/80">Risk Score</div>
        </div>
      </div>
    </div>
  );
};

// Loading Skeleton Component
const RiskHeroSkeleton: React.FC = () => {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-300 to-gray-400 p-6 shadow-xl animate-pulse">
      <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" />
      
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-8 w-8 bg-white/30 rounded" />
            <div>
              <div className="h-5 w-32 bg-white/30 rounded mb-2" />
              <div className="h-4 w-24 bg-white/20 rounded" />
            </div>
          </div>
          
          <div className="h-4 w-full bg-white/30 rounded mb-2" />
          <div className="h-4 w-3/4 bg-white/20 rounded mb-4" />
          
          <div className="h-4 w-48 bg-white/30 rounded mb-2" />
          <div className="h-3 w-32 bg-white/20 rounded mb-4" />
          
          <div className="h-12 w-48 bg-white/30 rounded" />
        </div>
        
        <div className="flex-shrink-0 ml-6">
          <div className="w-24 h-24 bg-white/30 rounded-full" />
        </div>
      </div>
    </div>
  );
};

// Error Component
const RiskHeroError: React.FC<{ onRetry: () => void }> = ({ onRetry }) => {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-500 to-red-600 p-6 text-white shadow-xl">
      <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" />
      
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="h-8 w-8" />
            <div>
              <h2 className="text-lg font-semibold">Risk Assessment Error</h2>
              <p className="text-sm text-white/80">Unable to load risk data</p>
            </div>
          </div>
          
          <p className="text-base mb-4 leading-relaxed">
            We encountered an issue loading your career risk assessment. Please try again.
          </p>
          
          <button
            onClick={onRetry}
            className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 rounded-lg px-6 py-3 text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/50"
            aria-label="Retry risk assessment"
          >
            Try Again
          </button>
        </div>
        
        <div className="flex-shrink-0 ml-6">
          <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center">
            <AlertTriangle className="h-8 w-8 text-white/60" />
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper Functions
const getCurrentUserProfile = (): any => {
  // This function should be implemented to get the current user's profile
  // For now, return a basic structure that matches the expected format
  return {
    personal_info: {
      age: 30,
      location: 'United States',
      education: 'Bachelor\'s Degree',
      employment: 'Full-time'
    },
    financial_info: {
      annual_income: 75000,
      monthly_takehome: 5000,
      student_loans: 25000,
      credit_card_debt: 5000,
      current_savings: 10000
    },
    monthly_expenses: {
      rent: 1500,
      car_payment: 400,
      insurance: 200,
      groceries: 400,
      utilities: 150,
      student_loan_payment: 300,
      credit_card_minimum: 150
    }
  };
};

const getCSRFToken = (): string => {
  // Get CSRF token from meta tag or cookie
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content') || '';
  }
  
  // Fallback to cookie
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return value;
    }
  }
  
  return '';
};

const trackAnalyticsEvent = async (eventType: string, eventData: any): Promise<void> => {
  try {
    const sessionId = getSessionId();
    const userId = getCurrentUserId();
    
    await fetch('/api/analytics/user-behavior/track-interaction', {
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
        element_id: 'risk-status-hero',
        element_text: 'Risk Status Hero Component',
        interaction_data: eventData
      })
    });
  } catch (error) {
    console.error('Failed to track analytics event:', error);
  }
};

const getSessionId = (): string => {
  // Get or create session ID
  let sessionId = sessionStorage.getItem('mingus_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('mingus_session_id', sessionId);
  }
  return sessionId;
};

const getCurrentUserId = (): string => {
  // Get current user ID from localStorage or session
  return localStorage.getItem('mingus_user_id') || 'anonymous';
};

export default RiskStatusHero;
