import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Star, ChevronDown, ChevronUp, ExternalLink, Target, Shield, Filter, RefreshCw } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import { useAuth, type AuthUserTier } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type { MarketConditionsPersonal, MarketConditionsResponse } from '../types/marketConditions';
import { interpolatePercentile, oesPercentilesFromPersonal } from '../utils/percentileUtils';

interface JobRecommendation {
  job: {
    job_id: string;
    title: string;
    company: string;
    location: string;
    msa?: string;
    salary_min: number;
    salary_max: number;
    salary_median: number;
    remote_friendly: boolean;
    url: string;
    description: string;
    requirements: string[];
    benefits: string[];
    field?: string;
    experience_level?: string;
    company_size?: string;
    company_industry?: string;
    equity_offered: boolean;
    bonus_potential: number;
    overall_score: number;
    diversity_score: number;
    growth_score: number;
    culture_score: number;
    career_advancement_score: number;
    work_life_balance_score: number;
  };
  tier: 'conservative' | 'same_level' | 'reach' | 'optimal' | 'stretch';
  success_probability: number;
  salary_increase_potential: number;
  skills_gap_analysis: Array<{
    skill: string;
    category: string;
    current_level: number;
    required_level: number;
    gap_size: number;
    priority: string;
    learning_time_estimate: string;
    resources: string[];
  }>;
  application_strategy: {
    approach: string;
    key_selling_points: string[];
    potential_challenges: string[];
    mitigation_strategies: string[];
  };
  preparation_roadmap: {
    immediate_actions: string[];
    short_term_goals: string[];
    long_term_goals: string[];
    skill_development_plan: string[];
    certification_recommendations: string[];
  };
  diversity_analysis: {
    diversity_score: number;
    inclusion_benefits: string[];
    company_diversity_metrics: Record<string, any>;
  };
  company_culture_fit: number;
  career_advancement_potential: number;
}

interface TierData {
  tier_name: string;
  tier_label: string;
  description: string;
  color_scheme: string;
  border_style: string;
  jobs: JobRecommendation[];
  average_salary_increase: number;
  average_success_rate: number;
  recommended_timeline: string;
  icon: React.ReactNode;
}

export interface CareerProfileSummary {
  current_role?: string | null;
  industry?: string | null;
  bls_career_field?: string | null;
  seniority_level?: string | null;
  profile_complete?: boolean;
}

type RecommendationViewState = 'loading' | 'upsell' | 'complete_profile' | 'coming_soon';

interface ApiJobItem {
  job_id?: string | number;
  title?: string;
  company?: string;
  location?: string;
  seniority_level?: string;
  salary_min?: number;
  salary_max?: number;
  salary_median?: number;
  advancement_trajectory?: string;
  url?: string;
  overall_score?: number;
  salary_increase_potential?: number;
  success_probability?: number;
}

interface ProcessResumeApiResponse {
  success?: boolean;
  error?: string;
  message?: string;
  recommendations?: {
    same_level?: ApiJobItem[];
    reach?: ApiJobItem[];
    conservative?: ApiJobItem[];
  };
}

const RECOMMENDATIONS_API = '/api/recommendations/process-resume';
const MARKET_CONDITIONS_API = '/api/market-conditions';
const CAREER_PROFILE_SUMMARY_API = '/api/career/profile-summary';

export type { MarketConditionsPersonal };

export interface PercentileData {
  status: 'ok' | 'no_career_data';
  current_salary?: number;
  percentile_bracket?: number;
  percentile_label?: string;
  percentiles?: { p10: number; p25: number; p50: number; p75: number; p90: number };
  zip_missing?: boolean;
  zip_prompt?: string;
  salary_missing?: boolean;
  salary_prompt?: string;
  bls_career_field?: string;
}

export function computePercentileBracket(
  salary: number,
  percentiles: PercentileData['percentiles']
): { bracket: number; label: string } | null {
  if (!percentiles || !salary) return null;
  const { p10, p25, p50, p75, p90 } = percentiles;
  if (salary >= p90) return { bracket: 90, label: '90th+ percentile' };
  if (salary >= p75) return { bracket: 75, label: '75th–90th percentile' };
  if (salary >= p50) return { bracket: 50, label: '50th–75th percentile' };
  if (salary >= p25) return { bracket: 25, label: '25th–50th percentile' };
  if (salary >= p10) return { bracket: 10, label: '10th–25th percentile' };
  return { bracket: 0, label: 'Below 10th percentile' };
}

function percentileToBracket(percentile: number): number {
  if (percentile >= 90) return 90;
  if (percentile >= 75) return 75;
  if (percentile >= 50) return 50;
  if (percentile >= 25) return 25;
  if (percentile >= 10) return 10;
  return 0;
}

function marketPersonalToPercentileData(personal: MarketConditionsPersonal): PercentileData {
  return {
    status: 'ok',
    current_salary: personal.current_salary,
    percentile_bracket: percentileToBracket(personal.percentile),
    percentile_label: `${personal.percentile}th percentile`,
    percentiles: {
      p10: personal.pct_10,
      p25: personal.pct_25,
      p50: personal.pct_50,
      p75: personal.pct_75,
      p90: personal.pct_90,
    },
    bls_career_field: personal.field_label,
  };
}

/** E2E / verify shim stored in localStorage when the session is cookie-backed. */
const PLACEHOLDER_ACCESS_TOKENS = new Set(['ok', '']);

function getCookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const parts = `; ${document.cookie}`.split(`; ${name}=`);
  if (parts.length < 2) return null;
  const raw = parts.pop()?.split(';').shift();
  return raw ? decodeURIComponent(raw) : null;
}

function isUsableJwt(token: string | null | undefined): token is string {
  if (!token || PLACEHOLDER_ACCESS_TOKENS.has(token)) return false;
  // Real mingus JWTs are HS256 strings with three segments.
  return token.split('.').length === 3;
}

/**
 * Resolve Bearer token for protected APIs. Live sessions often have auth_token='ok'
 * while the real JWT lives in the httpOnly mingus_token cookie (sent via credentials).
 * Never send Authorization: Bearer ok — the backend falls back to Bearer and rejects it.
 */
function resolveBearerToken(getAccessToken: () => string | null): string | null {
  const fromHook = getAccessToken();
  if (isUsableJwt(fromHook)) {
    return fromHook;
  }

  try {
    const fromMingusLs = localStorage.getItem('mingus_token');
    if (isUsableJwt(fromMingusLs)) {
      return fromMingusLs;
    }
    const fromAuthLs = localStorage.getItem('auth_token');
    if (isUsableJwt(fromAuthLs)) {
      return fromAuthLs;
    }
  } catch {
    /* ignore storage errors */
  }

  const fromCookie = getCookieValue('mingus_token');
  if (isUsableJwt(fromCookie)) {
    return fromCookie;
  }

  return null;
}

function buildAuthHeaders(getAccessToken: () => string | null): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
  };
  const token = resolveBearerToken(getAccessToken);
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function formatSalaryK(min?: number, max?: number): string {
  const fmt = (value: number) => `$${Math.round(value / 1000)}k`;
  if (min != null && max != null) {
    return `${fmt(min)} – ${fmt(max)}`;
  }
  if (min != null) {
    return fmt(min);
  }
  if (max != null) {
    return fmt(max);
  }
  return '—';
}

function formatSeniorityLabel(level?: string): string {
  if (!level) return '—';
  return level.charAt(0).toUpperCase() + level.slice(1);
}

const calculateAverageSalaryIncrease = (jobs: JobRecommendation[]): number => {
  if (jobs.length === 0) return 0;
  const total = jobs.reduce((sum, job) => sum + job.salary_increase_potential, 0);
  return Math.round(total / jobs.length);
};

const calculateAverageSuccessRate = (jobs: JobRecommendation[]): number => {
  if (jobs.length === 0) return 0;
  const total = jobs.reduce((sum, job) => sum + job.success_probability, 0);
  return Math.round(total / jobs.length);
};

function mapApiJobToRecommendation(
  raw: ApiJobItem,
  tier: 'conservative' | 'same_level' | 'reach'
): JobRecommendation {
  const salaryMin = raw.salary_min ?? 0;
  const salaryMax = raw.salary_max ?? 0;
  const salaryMedian =
    raw.salary_median ??
    (salaryMin && salaryMax ? Math.round((salaryMin + salaryMax) / 2) : 0);

  return {
    job: {
      job_id: String(raw.job_id ?? ''),
      title: raw.title ?? '',
      company: raw.company ?? '',
      location: raw.location ?? '',
      salary_min: salaryMin,
      salary_max: salaryMax,
      salary_median: salaryMedian,
      remote_friendly: false,
      url: raw.url ?? '',
      description: raw.advancement_trajectory ?? '',
      requirements: [],
      benefits: [],
      experience_level: raw.seniority_level,
      equity_offered: false,
      bonus_potential: 0,
      overall_score: raw.overall_score ?? 0,
      diversity_score: 0,
      growth_score: 0,
      culture_score: 0,
      career_advancement_score: 0,
      work_life_balance_score: 0,
    },
    tier,
    success_probability: raw.success_probability ?? 0,
    salary_increase_potential: raw.salary_increase_potential ?? 0,
    skills_gap_analysis: [],
    application_strategy: {
      approach: '',
      key_selling_points: [],
      potential_challenges: [],
      mitigation_strategies: [],
    },
    preparation_roadmap: {
      immediate_actions: [],
      short_term_goals: [],
      long_term_goals: [],
      skill_development_plan: [],
      certification_recommendations: [],
    },
    diversity_analysis: {
      diversity_score: 0,
      inclusion_benefits: [],
      company_diversity_metrics: {},
    },
    company_culture_fit: 0,
    career_advancement_potential: 0,
  };
}

function buildTiersFromApiResponse(
  recommendations: ProcessResumeApiResponse['recommendations']
): TierData[] {
  const tierDefs: Array<{
    key: 'conservative' | 'same_level' | 'reach';
    label: string;
    description: string;
    color_scheme: string;
    border_style: string;
    timeline: string;
    icon: React.ReactNode;
  }> = [
    {
      key: 'conservative',
      label: 'Safe Moves',
      description: 'Lower-risk roles aligned with your current trajectory',
      color_scheme: 'blue-600',
      border_style: 'border-2 border-blue-200 bg-blue-50',
      timeline: '1-3 mo',
      icon: <Shield className="h-6 w-6 text-blue-600" />,
    },
    {
      key: 'same_level',
      label: 'Right Level',
      description: 'Roles at your seniority with competitive compensation',
      color_scheme: 'purple-600',
      border_style: 'border-2 border-purple-200 bg-purple-50',
      timeline: '2-4 mo',
      icon: <Target className="h-6 w-6 text-purple-600" />,
    },
    {
      key: 'reach',
      label: 'Stretch Roles',
      description: 'Ambitious moves that stretch your skills and scope',
      color_scheme: 'orange-600',
      border_style: 'border-2 border-orange-200 bg-orange-50',
      timeline: '3-6 mo',
      icon: <Star className="h-6 w-6 text-orange-600" />,
    },
  ];

  return tierDefs.map((def) => {
    const rawJobs = recommendations?.[def.key] ?? [];
    const jobs = rawJobs.map((job) => mapApiJobToRecommendation(job, def.key));
    return {
      tier_name: def.key,
      tier_label: def.label,
      description: def.description,
      color_scheme: def.color_scheme,
      border_style: def.border_style,
      jobs,
      average_salary_increase: calculateAverageSalaryIncrease(jobs),
      average_success_rate: calculateAverageSuccessRate(jobs),
      recommended_timeline: def.timeline,
      icon: def.icon,
    };
  });
}

function allTiersEmpty(recommendations: ProcessResumeApiResponse['recommendations']): boolean {
  if (!recommendations) return true;
  return (
    (recommendations.conservative?.length ?? 0) === 0 &&
    (recommendations.same_level?.length ?? 0) === 0 &&
    (recommendations.reach?.length ?? 0) === 0
  );
}

interface RecommendationTiersProps {
  className?: string;
  userId?: string;
  locationRadius?: number;
  userTier?: AuthUserTier | null;
  careerProfile?: CareerProfileSummary | null;
  hideHeader?: boolean;
}

function isCareerProfileComplete(profile: CareerProfileSummary | null | undefined): boolean {
  if (!profile) return false;
  if (typeof profile.profile_complete === 'boolean') {
    return profile.profile_complete;
  }
  const role = profile.current_role?.trim();
  const industry = profile.industry?.trim();
  return Boolean(role && industry);
}

function resolveViewState(
  tier: AuthUserTier | null,
  careerProfile: CareerProfileSummary | null | undefined
): RecommendationViewState {
  if (tier === null) return 'loading';
  if (tier === 'budget') return 'upsell';
  if (!isCareerProfileComplete(careerProfile)) return 'complete_profile';
  return 'coming_soon';
}

const RecommendationTiers: React.FC<RecommendationTiersProps> = ({
  className = '',
  userId,
  locationRadius = 10,
  userTier: userTierProp,
  careerProfile,
  hideHeader = false,
}) => {
  const { userTier: authTier, loading: authLoading, getAccessToken } = useAuth();
  const effectiveTier = userTierProp ?? authTier;

  const [tiers, setTiers] = useState<TierData[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTier, setExpandedTier] = useState<string | null>('same_level');
  const [apiEmpty, setApiEmpty] = useState(false);
  const [apiProfileIncomplete, setApiProfileIncomplete] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedRadius, setSelectedRadius] = useState<number>(locationRadius);
  const [error, setError] = useState<string | null>(null);
  const [needsSignIn, setNeedsSignIn] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [percentileData, setPercentileData] = useState<PercentileData | null>(null);
  const [marketPersonal, setMarketPersonal] = useState<MarketConditionsPersonal | null>(null);
  const [fetchedCareerProfile, setFetchedCareerProfile] = useState<CareerProfileSummary | null>(
    null
  );

  const effectiveCareerProfile = careerProfile ?? fetchedCareerProfile;

  const { trackInteraction, trackError } = useAnalytics();

  const viewState = useMemo(
    () =>
      resolveViewState(
        authLoading && userTierProp == null ? null : effectiveTier,
        effectiveCareerProfile
      ),
    [authLoading, userTierProp, effectiveTier, effectiveCareerProfile]
  );

  const fetchRecommendations = useCallback(
    async (isRefresh = false) => {
      if (effectiveTier === 'budget') {
        setLoading(false);
        setIsRefreshing(false);
        setTiers([]);
        setApiEmpty(false);
        setApiProfileIncomplete(false);
        setError(null);
        return;
      }

      if (effectiveTier !== 'mid_tier' && effectiveTier !== 'professional') {
        return;
      }

      if (isRefresh) setIsRefreshing(true);
      setLoading(true);
      setError(null);
      setTiers([]);
      setApiEmpty(false);
      setApiProfileIncomplete(false);
      setNeedsSignIn(false);

      try {
        const response = await fetch(RECOMMENDATIONS_API, {
          method: 'POST',
          credentials: 'include',
          headers: buildAuthHeaders(getAccessToken),
          body: JSON.stringify({}),
        });

        if (response.status === 401) {
          setNeedsSignIn(true);
          setError('We could not verify your session for recommendations.');
          return;
        }

        let payload: ProcessResumeApiResponse = {};
        try {
          payload = (await response.json()) as ProcessResumeApiResponse;
        } catch {
          payload = {};
        }

        if (response.status === 422) {
          const errCode = payload.error ?? '';
          if (errCode === 'career_profile_incomplete' || response.status === 422) {
            setApiProfileIncomplete(true);
            return;
          }
        }

        if (!response.ok) {
          setError('Unable to load recommendations — try again');
          return;
        }

        const recommendations = payload.recommendations;
        if (allTiersEmpty(recommendations)) {
          setApiEmpty(true);
          setTiers(buildTiersFromApiResponse(recommendations));
        } else {
          setTiers(buildTiersFromApiResponse(recommendations));
        }

        setLastUpdated(new Date());

        await trackInteraction(
          isRefresh ? 'recommendations_refreshed' : 'recommendation_tiers_loaded',
          {
            view_state: viewState,
            radius_selected: selectedRadius,
            user_id: userId || getCurrentUserId(),
            has_results: !allTiersEmpty(recommendations),
          }
        );
      } catch (trackErr) {
        setError('Unable to load recommendations — try again');
        await trackError(trackErr instanceof Error ? trackErr : new Error(String(trackErr)), {
          component: 'RecommendationTiers',
          action: 'fetchRecommendations',
          radius: selectedRadius,
          userId: userId || getCurrentUserId(),
        });
      } finally {
        setLoading(false);
        setIsRefreshing(false);
      }
    },
    [effectiveTier, getAccessToken, selectedRadius, trackError, trackInteraction, userId]
  );

  useEffect(() => {
    if (authLoading && userTierProp == null) {
      return;
    }

    if (effectiveTier === 'budget') {
      setLoading(false);
      setTiers([]);
      setError(null);
      setApiEmpty(false);
      setApiProfileIncomplete(false);
      void Promise.resolve(
        trackInteraction('recommendation_tiers_loaded', {
          view_state: viewState,
          radius_selected: selectedRadius,
          user_id: userId || getCurrentUserId(),
        })
      ).catch((trackErr) => {
        console.error('Failed to track recommendation tiers load:', trackErr);
      });
      setLastUpdated(new Date());
      return;
    }

    if (effectiveTier === 'mid_tier' || effectiveTier === 'professional') {
      void fetchRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refetch only when tier/user changes
  }, [authLoading, userTierProp, effectiveTier, userId]);

  useEffect(() => {
    let cancelled = false;

    const fetchMarketConditions = async () => {
      try {
        const response = await fetch(MARKET_CONDITIONS_API, {
          credentials: 'include',
          headers: buildAuthHeaders(getAccessToken),
        });
        if (!response.ok || cancelled) return;

        const data = (await response.json()) as MarketConditionsResponse;
        if (!cancelled && data.personal) {
          setMarketPersonal(data.personal);
          setPercentileData(marketPersonalToPercentileData(data.personal));
        }
      } catch {
        /* silent — percentile UI stays hidden */
      }
    };

    void fetchMarketConditions();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  useEffect(() => {
    let cancelled = false;

    const fetchCareerProfileSummary = async () => {
      try {
        const response = await fetch(CAREER_PROFILE_SUMMARY_API, {
          credentials: 'include',
          headers: buildAuthHeaders(getAccessToken),
        });
        if (!response.ok || cancelled) return;

        const data = (await response.json()) as {
          profile?: {
            current_role?: string | null;
            industry?: string | null;
            seniority_level?: string | null;
            profile_complete?: boolean;
          };
        };
        if (!cancelled && data.profile) {
          const industry = data.profile.industry ?? null;
          setFetchedCareerProfile({
            current_role: data.profile.current_role,
            industry,
            bls_career_field: industry,
            seniority_level: data.profile.seniority_level ?? null,
            profile_complete: data.profile.profile_complete,
          });
        }
      } catch {
        /* silent — fall back to prop or incomplete state */
      }
    };

    void fetchCareerProfileSummary();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);
  
  const handleTierExpansion = async (tierName: string) => {
    const newExpandedTier = expandedTier === tierName ? null : tierName;
    setExpandedTier(newExpandedTier);
    
    // Track tier interaction using the hook
    await trackInteraction('recommendation_tier_expanded', {
      tier_name: tierName,
      action: newExpandedTier ? 'expanded' : 'collapsed',
      jobs_in_tier: tiers.find(t => t.tier_name === tierName)?.jobs.length || 0
    });
  };
  
  const handleJobInteraction = async (job: JobRecommendation, action: string) => {
    await trackInteraction('job_recommendation_interaction', {
      job_id: job.job.job_id,
      job_title: job.job.title,
      company: job.job.company,
      tier: job.tier,
      action: action,
      salary_increase: job.salary_increase_potential
    });
    
    if (action === 'apply_clicked') {
      // Navigate to application or external job posting
      if (job.job.url) {
        window.open(job.job.url, '_blank');
      } else {
        window.open(`/apply/${job.job.job_id}`, '_blank');
      }
    }
  };
  
  const handleRadiusChange = async (newRadius: number) => {
    setSelectedRadius(newRadius);
    await trackInteraction('location_radius_changed', {
      old_radius: selectedRadius,
      new_radius: newRadius
    });
  };
  
  const handleComparisonToggle = async () => {
    setComparisonMode(!comparisonMode);
    await trackInteraction('comparison_mode_toggled', {
      comparison_mode: !comparisonMode,
      expanded_tier: expandedTier
    });
  };
  
  const handleRefresh = async () => {
    await trackInteraction('recommendations_refreshed', {
      radius: selectedRadius,
      current_tiers: tiers.map(t => ({ name: t.tier_name, job_count: t.jobs.length }))
    });
    await fetchRecommendations(true);
  };
  
  if (loading || viewState === 'loading') {
    return <TierLoadingSkeleton />;
  }

  if (error) {
    return (
      <TierErrorState
        error={error}
        onRetry={fetchRecommendations}
        needsSignIn={needsSignIn}
      />
    );
  }

  const hasJobResults = tiers.some((t) => t.jobs.length > 0);

  return (
    <div className={`space-y-6 ${className}`}>
      {!hideHeader && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Career Recommendations</h2>
          <p className="text-gray-600">Roles matched to your career profile and location</p>
          {lastUpdated && (
            <p className="text-xs text-gray-500 mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      )}

      {viewState === 'upsell' && !hasJobResults && (
        <RecommendationStateCard
          title="Unlock Personalized Job Recommendations"
          body="Upgrade to Mid-Tier to see roles matched to your career profile and salary targets."
          ctaLabel="Upgrade to Mid-Tier"
          ctaTo="/upgrade"
          icon={<Shield className="h-10 w-10 text-purple-600" />}
          variant="upsell"
        />
      )}

      {apiProfileIncomplete && (
        <RecommendationStateCard
          title="Complete your career profile to see recommendations"
          body="Add your BLS career field, seniority level, and target compensation so we can match roles to you."
          ctaLabel="Complete Profile"
          ctaTo="/dashboard/tools?tab=you"
          icon={<Target className="h-10 w-10 text-gray-600" />}
          variant="profile"
        />
      )}

      {!apiProfileIncomplete && viewState === 'complete_profile' && !hasJobResults && (
        <RecommendationStateCard
          title="Complete Your Career Profile"
          body="Add your current role, industry, and target salary to see job recommendations tailored to you."
          ctaLabel="Complete Profile"
          ctaTo="/dashboard/tools?tab=you"
          icon={<Target className="h-10 w-10 text-gray-600" />}
          variant="profile"
        />
      )}

      {!apiProfileIncomplete &&
        viewState !== 'complete_profile' &&
        (apiEmpty || viewState === 'coming_soon') &&
        !hasJobResults && (
        <SourcingRolesEmptyState
          careerProfile={effectiveCareerProfile}
          percentileCareerField={percentileData?.bls_career_field}
        />
      )}

      {hasJobResults && (
        <>
          {percentileData?.status === 'ok' && percentileData.percentile_label && (
            <IncomeStandingBanner percentileData={percentileData} />
          )}
          {percentileData?.status === 'ok' &&
            !percentileData.percentile_label &&
            percentileData.salary_missing && (
            <IncomeSalaryPromptBanner percentileData={percentileData} />
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-end gap-3">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <select
                value={selectedRadius}
                onChange={(e) => handleRadiusChange(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Select search radius"
              >
                <option value={5}>5 miles</option>
                <option value={10}>10 miles</option>
                <option value={30}>30 miles</option>
                <option value={999}>Nationwide</option>
              </select>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="bg-blue-100 hover:bg-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed border border-blue-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none flex items-center gap-2"
              aria-label="Refresh recommendations"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
            <button
              onClick={handleComparisonToggle}
              className="bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
              aria-label={comparisonMode ? 'Exit comparison mode' : 'Enter comparison mode'}
            >
              {comparisonMode ? 'Exit Compare' : 'Compare Tiers'}
            </button>
          </div>

          <div className={`grid gap-6 ${comparisonMode ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {tiers.map((tier) => (
              <TierCard
                key={tier.tier_name}
                tier={tier}
                isExpanded={expandedTier === tier.tier_name}
                isComparison={comparisonMode}
                isFeatured={tier.tier_name === 'same_level'}
                onExpand={() => handleTierExpansion(tier.tier_name)}
                onJobInteraction={handleJobInteraction}
                percentileData={percentileData}
                marketPersonal={marketPersonal}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

const IncomeStandingBanner: React.FC<{ percentileData: PercentileData }> = ({
  percentileData,
}) => {
  const field = percentileData.bls_career_field ?? 'your field';
  const label = percentileData.percentile_label;
  if (!label) return null;

  return (
    <div className="rounded-lg border border-purple-100 bg-purple-50/80 px-4 py-3 text-sm text-slate-700">
      <p>
        You&apos;re currently in the{' '}
        <span className="font-medium text-purple-900">{label}</span> for{' '}
        <span className="font-medium text-slate-800">{field}</span>. The roles below could move
        you up.
      </p>
      {percentileData.zip_missing && (
        <p className="mt-1.5 text-xs text-slate-600">
          <Link
            to="/dashboard/tools?tab=you&focus=zip"
            className="font-medium text-purple-700 underline-offset-2 hover:text-purple-900 hover:underline"
          >
            Add your zip for local data →
          </Link>
        </p>
      )}
    </div>
  );
};

const IncomeSalaryPromptBanner: React.FC<{ percentileData: PercentileData }> = ({
  percentileData,
}) => {
  const field = percentileData.bls_career_field ?? 'your field';
  const median = percentileData.percentiles?.p50;
  const medianHint =
    median != null ? ` (national median ~$${Math.round(median / 1000)}k)` : '';

  return (
    <div className="rounded-lg border border-purple-100 bg-purple-50/80 px-4 py-3 text-sm text-slate-700">
      <p>
        {percentileData.salary_prompt ??
          'Add your income in Career Profile to see your percentile standing'}{' '}
        among{' '}
        <span className="font-medium text-slate-800">{field}</span>
        professionals{medianHint}.
      </p>
      <p className="mt-1.5 text-xs text-slate-600">
        <Link
          to="/dashboard/tools?tab=you&focus=income"
          className="font-medium text-purple-700 underline-offset-2 hover:text-purple-900 hover:underline"
        >
          Add income sources →
        </Link>
        {percentileData.zip_missing && (
          <>
            {' · '}
            <Link
              to="/dashboard/tools?tab=you&focus=zip"
              className="font-medium text-purple-700 underline-offset-2 hover:text-purple-900 hover:underline"
            >
              Add your zip for local data →
            </Link>
          </>
        )}
      </p>
    </div>
  );
};

function ProfileMatchField({ label, value }: { label: string; value: string | null | undefined }) {
  const trimmed = value?.trim();
  return (
    <p className="text-sm text-slate-700">
      {label}:{' '}
      {trimmed ? (
        <span className="font-medium text-slate-800">{trimmed}</span>
      ) : (
        <span className="font-medium text-amber-600">Not set ⚠️</span>
      )}
    </p>
  );
}

const SourcingRolesEmptyState: React.FC<{
  careerProfile: CareerProfileSummary | null | undefined;
  percentileCareerField?: string | null;
}> = ({ careerProfile, percentileCareerField }) => {
  const careerField =
    careerProfile?.bls_career_field?.trim() ||
    careerProfile?.industry?.trim() ||
    percentileCareerField?.trim() ||
    null;
  const seniority = careerProfile?.seniority_level?.trim() || null;

  return (
    <div className="rounded-xl border border-purple-100 bg-white p-6 shadow-sm sm:p-8">
      <div className="mx-auto max-w-lg text-left">
        <div className="mb-4 flex items-center gap-2">
          <Target className="h-6 w-6 shrink-0 text-purple-600" aria-hidden />
          <h3 className="text-lg font-semibold text-slate-900">
            🎯 We&apos;re matching roles to your profile
          </h3>
        </div>

        <div className="mb-5 space-y-1 rounded-lg border border-slate-100 bg-slate-50/80 px-4 py-3">
          <ProfileMatchField label="Your career field" value={careerField} />
          <ProfileMatchField
            label="Your level"
            value={seniority ? formatSeniorityLabel(seniority) : null}
          />
        </div>

        <p className="mb-2 text-sm font-medium text-slate-800">To improve your matches:</p>
        <ul className="mb-5 list-disc space-y-1 pl-5 text-sm text-slate-700">
          <li>Make sure your career field is set correctly</li>
          <li>Add your current role title if it&apos;s missing</li>
          <li>Check back — we add new roles weekly</li>
        </ul>

        <Link
          to="/dashboard/tools?tab=you"
          className="inline-flex items-center text-sm font-semibold text-purple-700 underline-offset-2 hover:text-purple-900 hover:underline"
        >
          Edit Career Profile →
        </Link>

        <p className="mt-5 text-xs leading-relaxed text-slate-500">
          Job matches are based on your career field and seniority level. The more complete your
          profile, the better your matches.
        </p>
      </div>
    </div>
  );
};

const RecommendationStateCard: React.FC<{
  title: string;
  body: string;
  ctaLabel?: string;
  ctaTo?: string;
  icon: React.ReactNode;
  variant: 'upsell' | 'profile' | 'holding';
}> = ({ title, body, ctaLabel, ctaTo, icon, variant }) => {
  const borderClass =
    variant === 'upsell'
      ? 'border-purple-300 bg-white shadow-sm'
      : 'border-gray-200 bg-white shadow-sm';

  const buttonClass =
    variant === 'upsell'
      ? 'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500'
      : 'bg-gray-900 hover:bg-gray-800 focus:ring-gray-500';

  return (
    <div className={`rounded-xl border p-8 text-center ${borderClass}`}>
      <div className="flex justify-center mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-700 max-w-lg mx-auto mb-6">{body}</p>
      {ctaLabel && ctaTo && (
        <Link
          to={ctaTo}
          className={`inline-block text-white px-6 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none ${buttonClass}`}
        >
          {ctaLabel}
        </Link>
      )}
    </div>
  );
};

// Individual Tier Card Component
const TierCard: React.FC<{
  tier: TierData;
  isExpanded: boolean;
  isComparison: boolean;
  isFeatured: boolean;
  onExpand: () => void;
  onJobInteraction: (job: JobRecommendation, action: string) => void;
  percentileData: PercentileData | null;
  marketPersonal: MarketConditionsPersonal | null;
}> = ({ tier, isExpanded, isComparison, isFeatured, onExpand, onJobInteraction, percentileData, marketPersonal }) => {
  
  return (
    <div 
      className={`
        relative rounded-xl transition-all duration-300 hover:shadow-lg
        ${tier.border_style}
        ${isFeatured ? 'ring-2 ring-purple-300 shadow-lg' : ''}
        ${isExpanded && !isComparison ? 'lg:col-span-3' : ''}
        focus-within:ring-2 focus-within:ring-blue-500 focus-within:outline-none
      `}
      role="region"
      aria-labelledby={`tier-${tier.tier_name}-title`}
    >
      {/* Featured Badge */}
      {isFeatured && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <div className="bg-purple-600 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
            <Star className="h-3 w-3" />
            RECOMMENDED
          </div>
        </div>
      )}
      
      {/* Card Header */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`text-${tier.color_scheme}`}>
              {tier.icon}
            </div>
            <div>
              <h3 
                id={`tier-${tier.tier_name}-title`}
                className={`text-lg font-semibold text-${tier.color_scheme}`}
              >
                {tier.tier_label}
              </h3>
              <p className="text-sm text-gray-600">{tier.description}</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {tier.jobs.length}
            </div>
            <div className="text-xs text-gray-500">opportunities</div>
          </div>
        </div>
        
        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              +{tier.average_salary_increase}%
            </div>
            <div className="text-xs text-gray-500">Avg Increase</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              {tier.average_success_rate}%
            </div>
            <div className="text-xs text-gray-500">Success Rate</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              {tier.recommended_timeline}
            </div>
            <div className="text-xs text-gray-500">Timeline</div>
          </div>
        </div>
        
        {/* Job Previews */}
        {tier.jobs.length > 0 && (
          <div className="space-y-2 mb-4">
            {tier.jobs.slice(0, isComparison ? 1 : 2).map((job) => (
              <JobPreviewCard
                key={job.job.job_id}
                job={job}
                onInteraction={onJobInteraction}
                compact={isComparison}
                percentileData={percentileData}
                marketPersonal={marketPersonal}
              />
            ))}
          </div>
        )}
        
        {/* Expand Button */}
        {tier.jobs.length > 0 && !isComparison && (
          <button
            onClick={onExpand}
            className={`
              w-full flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors
              bg-${tier.color_scheme}/10 hover:bg-${tier.color_scheme}/20 text-${tier.color_scheme}
              focus:ring-2 focus:ring-${tier.color_scheme}/50 focus:outline-none
            `}
            aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${tier.tier_label} tier`}
          >
            {isExpanded ? (
              <>Show Less <ChevronUp className="h-4 w-4" /></>
            ) : (
              <>View All {tier.jobs.length} Opportunities <ChevronDown className="h-4 w-4" /></>
            )}
          </button>
        )}
      </div>
      
      {/* Expanded Job List */}
      {isExpanded && !isComparison && tier.jobs.length > 2 && (
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="grid gap-3">
            {tier.jobs.slice(2).map((job) => (
              <JobPreviewCard
                key={job.job.job_id}
                job={job}
                onInteraction={onJobInteraction}
                compact={false}
                percentileData={percentileData}
                marketPersonal={marketPersonal}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Job Preview Card Component
const JobPreviewCard: React.FC<{
  job: JobRecommendation;
  onInteraction: (job: JobRecommendation, action: string) => void;
  compact: boolean;
  percentileData: PercentileData | null;
  marketPersonal: MarketConditionsPersonal | null;
}> = ({ job, onInteraction, compact, marketPersonal }) => {
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'conservative': return 'blue';
      case 'same_level':
      case 'optimal': return 'purple';
      case 'reach':
      case 'stretch': return 'orange';
      default: return 'gray';
    }
  };

  const tierColor = getTierColor(job.tier);
  const advancement = job.job.description?.trim();

  const percentileLiftLine = useMemo(() => {
    if (!marketPersonal || !job.job.salary_max || job.job.salary_max <= 0) {
      return null;
    }

    const bands = oesPercentilesFromPersonal(marketPersonal);
    const targetPercentile = interpolatePercentile(job.job.salary_max, bands);
    if (targetPercentile <= marketPersonal.percentile) {
      return null;
    }

    return `This role would move you from the ${marketPersonal.percentile}th to the ${targetPercentile}th percentile for ${marketPersonal.field_label} in ${marketPersonal.msa_name}`;
  }, [job.job.salary_max, marketPersonal]);

  return (
    <div 
      className={`bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow ${compact ? 'text-sm' : ''} touch-manipulation`}
      role="article"
      aria-labelledby={`job-${job.job.job_id}-title`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 
            id={`job-${job.job.job_id}-title`}
            className={`font-semibold text-gray-900 ${compact ? 'text-sm' : 'text-base'} truncate`}
          >
            {job.job.title}
          </h4>
          <p className={`text-gray-600 ${compact ? 'text-xs' : 'text-sm'} truncate`}>
            {job.job.company}
          </p>
        </div>
      </div>

      <div className="space-y-1 text-sm text-gray-600 mb-3">
        <p>
          <span className="font-medium text-gray-700">Seniority: </span>
          {formatSeniorityLabel(job.job.experience_level)}
        </p>
        <p className="font-medium text-gray-900">
          {formatSalaryK(job.job.salary_min, job.job.salary_max)}
        </p>
        {percentileLiftLine ? (
          <p className="text-xs text-green-700">{percentileLiftLine}</p>
        ) : null}
        {advancement ? (
          <p className="text-gray-600">
            <span className="font-medium text-gray-700">Next step: </span>
            {advancement}
          </p>
        ) : null}
      </div>
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="text-sm text-gray-500 truncate">
          {job.job.location || null}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => onInteraction(job, 'view_details')}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none rounded px-2 py-1"
            aria-label={`View details for ${job.job.title} at ${job.job.company}`}
          >
            View Details
          </button>
          <button
            onClick={() => onInteraction(job, 'apply_clicked')}
            className={`bg-${tierColor}-600 hover:bg-${tierColor}-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors flex items-center gap-1 focus:ring-2 focus:ring-${tierColor}-500 focus:outline-none touch-manipulation`}
            aria-label={`Apply to ${job.job.title} at ${job.job.company}`}
          >
            Apply
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Loading Skeleton Component
const TierLoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-gray-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
                <div>
                  <div className="h-5 w-32 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="h-4 w-48 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
              <div className="text-right">
                <div className="h-8 w-8 bg-gray-200 rounded animate-pulse mb-1" />
                <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[1, 2, 3].map((j) => (
                <div key={j} className="text-center">
                  <div className="h-6 w-12 bg-gray-200 rounded animate-pulse mx-auto mb-1" />
                  <div className="h-3 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                </div>
              ))}
            </div>
            
            <div className="space-y-2">
              {[1, 2].map((j) => (
                <div key={j} className="bg-gray-100 rounded-lg p-3">
                  <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="flex justify-between">
                    <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
                    <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Error State Component
const TierErrorState: React.FC<{
  error: string;
  onRetry: () => void;
  needsSignIn?: boolean;
}> = ({ error, onRetry, needsSignIn = false }) => {
  return (
    <div className="text-center py-12 bg-red-50 rounded-xl border border-red-200">
      <div className="text-red-400 mb-4">
        <Target className="h-12 w-12 mx-auto" />
      </div>
      <h3 className="text-lg font-semibold text-red-900 mb-2">Unable to load recommendations</h3>
      <p className="text-red-700 mb-4">{error}</p>
      {needsSignIn ? (
        <Link
          to="/login"
          className="inline-block bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-red-500 focus:outline-none"
        >
          Sign in again
        </Link>
      ) : (
        <button
          onClick={onRetry}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-red-500 focus:outline-none"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

const getCurrentUserId = (): string => {
  return localStorage.getItem('mingus_user_id') || 'anonymous';
};

export default RecommendationTiers;
