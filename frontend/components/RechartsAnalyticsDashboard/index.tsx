import React, { useState, useEffect } from 'react';
import { 
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    AreaChart, Area, ComposedChart
} from 'recharts';
import { 
    TrendingUp, Users, BookOpen, Target, Search, Award, 
    RefreshCw, Calendar, Eye, CheckCircle, Bookmark, Share
} from 'lucide-react';

interface DashboardData {
    period_days: number;
    user_engagement: {
        active_users: number;
        avg_session_time_minutes: number;
        total_article_views: number;
        total_completions: number;
        avg_search_success_rate: number;
        avg_session_duration_minutes: number;
        total_sessions: number;
        avg_articles_per_session: number;
    };
    top_articles: Array<{
        title: string;
        phase: string;
        views: number;
        completion_rate: number;
        cultural_engagement: number;
    }>;
    phase_performance: Array<{
        phase: string;
        article_count: number;
        total_views: number;
        avg_completion_rate: number;
    }>;
    cultural_effectiveness: {
        high_relevance_preference: number;
        community_engagement: number;
        cultural_completion_rate: number;
    };
    search_behavior: {
        total_searches: number;
        click_through_rate: number;
        cultural_search_percentage: number;
    };
}

interface UserJourneyData {
    assessment_distribution: Array<{
        level: string;
        user_count: number;
        avg_be_score: number;
        avg_do_score: number;
        avg_have_score: number;
    }>;
    content_access_patterns: Array<{
        difficulty: string;
        phase: string;
        unique_readers: number;
    }>;
    transformation_journey: Array<{
        current_phase: string;
        user_count: number;
        avg_phase_duration_days: number;
        avg_be_articles: number;
        avg_do_articles: number;
        avg_have_articles: number;
    }>;
}

interface CulturalImpactData {
    content_performance_comparison: Array<{
        content_type: string;
        avg_completion_rate: number;
        avg_bookmark_rate: number;
        avg_rating: number;
        article_count: number;
    }>;
    cultural_engagement_summary: {
        preference_score: number;
        engagement_score: number;
        users_tracked: number;
        avg_cultural_searches: number;
    };
    cultural_search_analysis: {
        cultural_searches: number;
        total_searches: number;
        cultural_search_percentage: number;
        cultural_search_success_rate: number;
    };
}

const AnalyticsDashboard: React.FC = () => {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [userJourneyData, setUserJourneyData] = useState<UserJourneyData | null>(null);
    const [culturalImpactData, setCulturalImpactData] = useState<CulturalImpactData | null>(null);
    const [timeRange, setTimeRange] = useState(30);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

    useEffect(() => {
        loadAnalyticsData();
    }, [timeRange]);

    // Auto-refresh every 5 minutes
    useEffect(() => {
        const interval = setInterval(() => {
            loadAnalyticsData();
        }, 300000); // 5 minutes

        return () => clearInterval(interval);
    }, []);

    const loadAnalyticsData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const [dashboardResponse, journeyResponse, culturalResponse] = await Promise.all([
                fetch(`/api/analytics/dashboard?days=${timeRange}`, {
                    headers: { 
                        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                }),
                fetch('/api/analytics/user-journey', {
                    headers: { 
                        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                }),
                fetch('/api/analytics/cultural-impact', {
                    headers: { 
                        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                })
            ]);
            
            if (!dashboardResponse.ok || !journeyResponse.ok || !culturalResponse.ok) {
                throw new Error('Failed to fetch analytics data');
            }
            
            const dashboardData = await dashboardResponse.json();
            const journeyData = await journeyResponse.json();
            const culturalData = await culturalResponse.json();
            
            setDashboardData(dashboardData);
            setUserJourneyData(journeyData);
            setCulturalImpactData(culturalData);
            setLastUpdated(new Date());
            
        } catch (error) {
            console.error('Failed to load analytics data:', error);
            setError('Failed to load analytics data. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const COLORS = {
        BE: '#1E3A8A',    // Deep Blue
        DO: '#059669',    // Emerald Green  
        HAVE: '#D97706',  // Golden Yellow
        cultural: '#7C3AED', // Purple
        general: '#6B7280',   // Gray
        high: '#DC2626',  // Red for high cultural relevance
        standard: '#6B7280'   // Gray for standard content
    };

    const formatNumber = (num: number) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    };

    const formatPercentage = (num: number) => {
        return `${num.toFixed(1)}%`;
    };

    if (loading && !dashboardData) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error loading analytics</h3>
                            <p className="text-sm text-red-700 mt-1">{error}</p>
                            <button 
                                onClick={loadAnalyticsData}
                                className="mt-2 text-sm text-red-800 hover:text-red-900 underline"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            📊 Article Library Analytics
                        </h1>
                        <p className="text-gray-600 mt-1">
                            Performance insights for African American professional content
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                            Last updated: {lastUpdated.toLocaleString()}
                        </p>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(parseInt(e.target.value))}
                            className="border rounded-lg px-3 py-2 bg-white"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>
                        <button
                            onClick={loadAnalyticsData}
                            disabled={loading}
                            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <MetricCard
                    title="Active Users"
                    value={formatNumber(dashboardData?.user_engagement?.active_users || 0)}
                    icon={Users}
                    color="blue"
                    subtitle={`${dashboardData?.user_engagement?.total_sessions || 0} sessions`}
                />
                <MetricCard
                    title="Article Views"
                    value={formatNumber(dashboardData?.user_engagement?.total_article_views || 0)}
                    icon={BookOpen}
                    color="green"
                    subtitle={`${dashboardData?.user_engagement?.total_completions || 0} completions`}
                />
                <MetricCard
                    title="Avg Session (min)"
                    value={dashboardData?.user_engagement?.avg_session_time_minutes?.toFixed(1) || '0'}
                    icon={TrendingUp}
                    color="purple"
                    subtitle={`${dashboardData?.user_engagement?.avg_articles_per_session?.toFixed(1) || '0'} articles/session`}
                />
                <MetricCard
                    title="Search Success Rate"
                    value={formatPercentage(dashboardData?.user_engagement?.avg_search_success_rate || 0)}
                    icon={Search}
                    color="yellow"
                    subtitle={`${formatNumber(dashboardData?.search_behavior?.total_searches || 0)} total searches`}
                />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* Be-Do-Have Performance */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Target className="w-5 h-5 mr-2 text-purple-600" />
                        Be-Do-Have Phase Performance
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <ComposedChart data={dashboardData?.phase_performance || []}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="phase" />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip 
                                formatter={(value, name) => [
                                    name === 'total_views' ? formatNumber(value as number) : `${value}%`,
                                    name === 'total_views' ? 'Total Views' : 'Completion Rate'
                                ]}
                            />
                            <Bar 
                                yAxisId="left"
                                dataKey="total_views" 
                                fill="#7C3AED" 
                                name="total_views"
                                radius={[4, 4, 0, 0]}
                            />
                            <Line 
                                yAxisId="right"
                                type="monotone" 
                                dataKey="avg_completion_rate" 
                                stroke="#059669" 
                                strokeWidth={3}
                                name="avg_completion_rate"
                                dot={{ fill: '#059669', strokeWidth: 2, r: 4 }}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>

                {/* Cultural Content Effectiveness */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Award className="w-5 h-5 mr-2 text-purple-600" />
                        Cultural vs Standard Content Performance
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={culturalImpactData?.content_performance_comparison || []}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="content_type" />
                            <YAxis />
                            <Tooltip formatter={(value) => [`${value}%`, 'Rate']} />
                            <Legend />
                            <Bar 
                                dataKey="avg_completion_rate" 
                                fill="#7C3AED" 
                                name="Completion Rate %"
                                radius={[4, 4, 0, 0]}
                            />
                            <Bar 
                                dataKey="avg_bookmark_rate" 
                                fill="#D97706" 
                                name="Bookmark Rate %"
                                radius={[4, 4, 0, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* User Journey Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* Assessment Distribution */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Users className="w-5 h-5 mr-2 text-purple-600" />
                        User Assessment Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={userJourneyData?.assessment_distribution || []}
                                dataKey="user_count"
                                nameKey="level"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label={({ level, user_count }) => `${level}: ${user_count}`}
                            >
                                {(userJourneyData?.assessment_distribution || []).map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={Object.values(COLORS)[index % Object.keys(COLORS).length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value) => [value, 'Users']} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Top Performing Articles */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <BookOpen className="w-5 h-5 mr-2 text-purple-600" />
                        Top Performing Articles
                    </h3>
                    <div className="space-y-4">
                        {(dashboardData?.top_articles || []).slice(0, 5).map((article, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex-grow">
                                    <h4 className="font-medium text-gray-900 truncate">
                                        {article.title}
                                    </h4>
                                    <div className="flex items-center space-x-2 mt-1">
                                        <span className={`
                                            px-2 py-1 rounded-full text-xs font-medium
                                            ${article.phase === 'BE' ? 'bg-blue-100 text-blue-800' :
                                              article.phase === 'DO' ? 'bg-green-100 text-green-800' :
                                              'bg-yellow-100 text-yellow-800'}
                                        `}>
                                            {article.phase}
                                        </span>
                                        <span className="text-sm text-gray-600">
                                            {formatNumber(article.views)} views • {article.completion_rate}% completion
                                        </span>
                                        {article.cultural_engagement > 7 && (
                                            <span className="text-xs text-purple-600 font-medium">
                                                🌟 High Cultural Engagement
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Cultural Impact Summary */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border p-6 mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    🌟 Cultural Personalization Impact
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">
                            {culturalImpactData?.cultural_engagement_summary?.preference_score?.toFixed(1) || 0}/10
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                            Cultural Preference Score
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">
                            {culturalImpactData?.cultural_engagement_summary?.engagement_score?.toFixed(1) || 0}/10
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                            Community Engagement Score
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">
                            {formatPercentage(culturalImpactData?.cultural_search_analysis?.cultural_search_percentage || 0)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                            Cultural Search Percentage
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">
                            {culturalImpactData?.cultural_engagement_summary?.users_tracked || 0}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                            Users with Cultural Analytics
                        </div>
                    </div>
                </div>
            </div>

            {/* Search Behavior Analysis */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Search className="w-5 h-5 mr-2 text-purple-600" />
                    Search Behavior Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                            {formatNumber(dashboardData?.search_behavior?.total_searches || 0)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">Total Searches</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                            {formatPercentage(dashboardData?.search_behavior?.click_through_rate || 0)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">Click-Through Rate</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                            {formatPercentage(dashboardData?.search_behavior?.cultural_search_percentage || 0)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">Cultural Search %</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

interface MetricCardProps {
    title: string;
    value: string;
    icon: React.ComponentType<any>;
    color: 'blue' | 'green' | 'purple' | 'yellow';
    subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, color, subtitle }) => {
    const colorClasses = {
        blue: 'bg-blue-50 text-blue-600',
        green: 'bg-green-50 text-green-600',
        purple: 'bg-purple-50 text-purple-600',
        yellow: 'bg-yellow-50 text-yellow-600'
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-gray-600">{title}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
                    {subtitle && (
                        <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
                    )}
                </div>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
