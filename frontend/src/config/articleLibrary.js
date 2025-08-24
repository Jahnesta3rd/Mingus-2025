/**
 * MINGUS Article Library - Frontend Configuration
 * ===============================================
 * Centralized configuration for the article library React components
 */

// =====================================================
// API CONFIGURATION
// =====================================================

const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000',
  WS_URL: process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:5000',
  VERSION: process.env.REACT_APP_API_VERSION || 'v1',
  TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000,
  ENDPOINTS: {
    ARTICLES: process.env.REACT_APP_ARTICLES_API_BASE || '/api/articles',
    SEARCH: process.env.REACT_APP_ARTICLES_SEARCH_ENDPOINT || '/api/articles/search',
    RECOMMENDATIONS: process.env.REACT_APP_ARTICLES_RECOMMENDATIONS_ENDPOINT || '/api/articles/recommendations',
    ANALYTICS: process.env.REACT_APP_ARTICLES_ANALYTICS_ENDPOINT || '/api/articles/analytics',
    FOLDERS: process.env.REACT_APP_ARTICLES_FOLDERS_ENDPOINT || '/api/articles/folders',
    TOPICS: process.env.REACT_APP_ARTICLES_TOPICS_ENDPOINT || '/api/articles/topics',
    FILTERS: process.env.REACT_APP_ARTICLES_FILTERS_ENDPOINT || '/api/articles/filters',
    AUTH: process.env.REACT_APP_AUTH_ENDPOINT || '/api/auth',
  }
};

// =====================================================
// FEATURE FLAGS
// =====================================================

const FEATURE_FLAGS = {
  ARTICLE_LIBRARY: process.env.REACT_APP_ENABLE_ARTICLE_LIBRARY === 'true',
  AI_RECOMMENDATIONS: process.env.REACT_APP_ENABLE_AI_RECOMMENDATIONS === 'true',
  CULTURAL_PERSONALIZATION: process.env.REACT_APP_ENABLE_CULTURAL_PERSONALIZATION === 'true',
  ADVANCED_SEARCH: process.env.REACT_APP_ENABLE_ADVANCED_SEARCH === 'true',
  SOCIAL_SHARING: process.env.REACT_APP_ENABLE_SOCIAL_SHARING === 'true',
  OFFLINE_MODE: process.env.REACT_APP_ENABLE_OFFLINE_MODE === 'true',
  ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  ARTICLE_FOLDERS: process.env.REACT_APP_ENABLE_ARTICLE_FOLDERS === 'true',
  ARTICLE_BOOKMARKS: process.env.REACT_APP_ENABLE_ARTICLE_BOOKMARKS === 'true',
  ARTICLE_NOTES: process.env.REACT_APP_ENABLE_ARTICLE_NOTES === 'true',
  ARTICLE_EXPORT: process.env.REACT_APP_ENABLE_ARTICLE_EXPORT === 'true',
  ARTICLE_IMPORT: process.env.REACT_APP_ENABLE_ARTICLE_IMPORT === 'true',
};

// =====================================================
// UI CONFIGURATION
// =====================================================

const UI_CONFIG = {
  ITEMS_PER_PAGE: parseInt(process.env.REACT_APP_ITEMS_PER_PAGE) || 20,
  SEARCH_DEBOUNCE_MS: parseInt(process.env.REACT_APP_SEARCH_DEBOUNCE_MS) || 300,
  ANIMATION_DURATION: parseInt(process.env.REACT_APP_ANIMATION_DURATION) || 200,
  TOAST_DURATION: parseInt(process.env.REACT_APP_TOAST_DURATION) || 5000,
  LOADING_TIMEOUT: parseInt(process.env.REACT_APP_LOADING_TIMEOUT) || 10000,
  INFINITE_SCROLL_THRESHOLD: parseInt(process.env.REACT_APP_INFINITE_SCROLL_THRESHOLD) || 100,
  THEME: process.env.REACT_APP_THEME || 'light',
  PRIMARY_COLOR: process.env.REACT_APP_PRIMARY_COLOR || '#3B82F6',
  SECONDARY_COLOR: process.env.REACT_APP_SECONDARY_COLOR || '#10B981',
  ACCENT_COLOR: process.env.REACT_APP_ACCENT_COLOR || '#F59E0B',
  DARK_MODE_ENABLED: process.env.REACT_APP_DARK_MODE_ENABLED === 'true',
  CUSTOM_FONTS_ENABLED: process.env.REACT_APP_CUSTOM_FONTS_ENABLED === 'true',
};

// =====================================================
// SEARCH & FILTERING CONFIGURATION
// =====================================================

const SEARCH_CONFIG = {
  MIN_LENGTH: parseInt(process.env.REACT_APP_SEARCH_MIN_LENGTH) || 2,
  MAX_RESULTS: parseInt(process.env.REACT_APP_SEARCH_MAX_RESULTS) || 100,
  DEBOUNCE_MS: parseInt(process.env.REACT_APP_FILTER_DEBOUNCE_MS) || 500,
  HISTORY_LIMIT: parseInt(process.env.REACT_APP_SEARCH_HISTORY_LIMIT) || 10,
  SUGGESTIONS_LIMIT: parseInt(process.env.REACT_APP_SEARCH_SUGGESTIONS_LIMIT) || 5,
  FILTERS: {
    CATEGORIES: ['Be', 'Do', 'Have'],
    DIFFICULTY_LEVELS: ['Beginner', 'Intermediate', 'Advanced'],
    CULTURAL_RELEVANCE: ['Low', 'Medium', 'High'],
    READING_TIME: ['Quick Read', 'Medium Read', 'Long Read'],
    PUBLICATION_DATE: ['Last 24 hours', 'Last week', 'Last month', 'Last year'],
  },
  SORT_OPTIONS: [
    { value: 'relevance', label: 'Relevance' },
    { value: 'date', label: 'Publication Date' },
    { value: 'title', label: 'Title' },
    { value: 'reading_time', label: 'Reading Time' },
    { value: 'cultural_relevance', label: 'Cultural Relevance' },
    { value: 'popularity', label: 'Popularity' },
  ],
};

// =====================================================
// ASSESSMENT & PERSONALIZATION CONFIGURATION
// =====================================================

const ASSESSMENT_CONFIG = {
  CACHE_DURATION: parseInt(process.env.REACT_APP_ASSESSMENT_CACHE_DURATION) || 7200,
  THRESHOLDS: {
    BE: {
      INTERMEDIATE: parseInt(process.env.REACT_APP_BE_INTERMEDIATE_THRESHOLD) || 60,
      ADVANCED: parseInt(process.env.REACT_APP_BE_ADVANCED_THRESHOLD) || 80,
    },
    DO: {
      INTERMEDIATE: parseInt(process.env.REACT_APP_DO_INTERMEDIATE_THRESHOLD) || 60,
      ADVANCED: parseInt(process.env.REACT_APP_DO_ADVANCED_THRESHOLD) || 80,
    },
    HAVE: {
      INTERMEDIATE: parseInt(process.env.REACT_APP_HAVE_INTERMEDIATE_THRESHOLD) || 60,
      ADVANCED: parseInt(process.env.REACT_APP_HAVE_ADVANCED_THRESHOLD) || 80,
    },
  },
  CULTURAL_RELEVANCE_THRESHOLD: parseFloat(process.env.REACT_APP_CULTURAL_RELEVANCE_THRESHOLD) || 6.0,
  FRAMEWORKS: {
    BE: {
      name: 'Be',
      description: 'Personal development and mindset',
      color: '#3B82F6',
      icon: '🧠',
    },
    DO: {
      name: 'Do',
      description: 'Actions and behaviors',
      color: '#10B981',
      icon: '⚡',
    },
    HAVE: {
      name: 'Have',
      description: 'Resources and achievements',
      color: '#F59E0B',
      icon: '🏆',
    },
  },
};

// =====================================================
// CACHING & PERFORMANCE CONFIGURATION
// =====================================================

const CACHE_CONFIG = {
  ENABLED: process.env.REACT_APP_CACHE_ENABLED === 'true',
  DURATION: parseInt(process.env.REACT_APP_CACHE_DURATION) || 3600,
  ARTICLE_CACHE_DURATION: parseInt(process.env.REACT_APP_ARTICLE_CACHE_DURATION) || 1800,
  SEARCH_CACHE_DURATION: parseInt(process.env.REACT_APP_SEARCH_CACHE_DURATION) || 900,
  RECOMMENDATIONS_CACHE_DURATION: parseInt(process.env.REACT_APP_RECOMMENDATIONS_CACHE_DURATION) || 3600,
  IMAGE_CACHE_DURATION: parseInt(process.env.REACT_APP_IMAGE_CACHE_DURATION) || 86400,
  KEYS: {
    ARTICLES: 'mingus_articles',
    SEARCH: 'mingus_search',
    RECOMMENDATIONS: 'mingus_recommendations',
    USER_PREFERENCES: 'mingus_user_preferences',
    ASSESSMENT_SCORES: 'mingus_assessment_scores',
  },
};

// =====================================================
// AUTHENTICATION CONFIGURATION
// =====================================================

const AUTH_CONFIG = {
  JWT_STORAGE_KEY: process.env.REACT_APP_JWT_STORAGE_KEY || 'mingus_jwt_token',
  REFRESH_TOKEN_KEY: process.env.REACT_APP_REFRESH_TOKEN_KEY || 'mingus_refresh_token',
  TIMEOUT: parseInt(process.env.REACT_APP_AUTH_TIMEOUT) || 3600000,
  AUTO_REFRESH: process.env.REACT_APP_AUTO_REFRESH === 'true',
  ENDPOINTS: {
    LOGIN: '/login',
    LOGOUT: '/logout',
    REFRESH: '/refresh',
    REGISTER: '/register',
    FORGOT_PASSWORD: '/forgot-password',
    RESET_PASSWORD: '/reset-password',
    VERIFY_EMAIL: '/verify-email',
  },
};

// =====================================================
// SOCIAL SHARING CONFIGURATION
// =====================================================

const SOCIAL_CONFIG = {
  ENABLED: process.env.REACT_APP_SOCIAL_SHARING_ENABLED === 'true',
  PLATFORMS: {
    TWITTER: {
      ENABLED: process.env.REACT_APP_TWITTER_SHARE_ENABLED === 'true',
      URL: 'https://twitter.com/intent/tweet',
      PARAMS: {
        text: '',
        url: '',
        hashtags: 'MingusArticles,PersonalDevelopment',
      },
    },
    FACEBOOK: {
      ENABLED: process.env.REACT_APP_FACEBOOK_SHARE_ENABLED === 'true',
      URL: 'https://www.facebook.com/sharer/sharer.php',
      PARAMS: {
        u: '',
        quote: '',
      },
    },
    LINKEDIN: {
      ENABLED: process.env.REACT_APP_LINKEDIN_SHARE_ENABLED === 'true',
      URL: 'https://www.linkedin.com/sharing/share-offsite',
      PARAMS: {
        url: '',
        title: '',
        summary: '',
      },
    },
    EMAIL: {
      ENABLED: process.env.REACT_APP_EMAIL_SHARE_ENABLED === 'true',
      SUBJECT: 'Check out this article from Mingus',
      BODY_TEMPLATE: 'I found this interesting article: {title}\n\n{url}\n\nShared via Mingus Article Library',
    },
  },
};

// =====================================================
// ANALYTICS & TRACKING CONFIGURATION
// =====================================================

const ANALYTICS_CONFIG = {
  ENABLED: process.env.REACT_APP_ANALYTICS_ENABLED === 'true',
  GOOGLE_ANALYTICS_ID: process.env.REACT_APP_GOOGLE_ANALYTICS_ID || '',
  MIXPANEL_TOKEN: process.env.REACT_APP_MIXPANEL_TOKEN || '',
  HOTJAR_ID: process.env.REACT_APP_HOTJAR_ID || '',
  CRISP_CHAT_ID: process.env.REACT_APP_CRISP_CHAT_ID || '',
  EVENTS: {
    ARTICLE_VIEW: 'article_view',
    ARTICLE_SHARE: 'article_share',
    ARTICLE_BOOKMARK: 'article_bookmark',
    SEARCH_PERFORMED: 'search_performed',
    FILTER_APPLIED: 'filter_applied',
    RECOMMENDATION_CLICKED: 'recommendation_clicked',
    ASSESSMENT_COMPLETED: 'assessment_completed',
  },
};

// =====================================================
// ERROR HANDLING & MONITORING CONFIGURATION
// =====================================================

const ERROR_CONFIG = {
  ERROR_BOUNDARY_ENABLED: process.env.REACT_APP_ERROR_BOUNDARY_ENABLED === 'true',
  SENTRY_DSN: process.env.REACT_APP_SENTRY_DSN || '',
  LOG_ROCKET_APP_ID: process.env.REACT_APP_LOG_ROCKET_APP_ID || '',
  BUGSNAG_API_KEY: process.env.REACT_APP_BUGSNAG_API_KEY || '',
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  TIMEOUT_MESSAGES: {
    API_TIMEOUT: 'Request timed out. Please try again.',
    NETWORK_ERROR: 'Network error. Please check your connection.',
    SERVER_ERROR: 'Server error. Please try again later.',
    UNAUTHORIZED: 'Please log in to continue.',
    FORBIDDEN: 'You do not have permission to perform this action.',
  },
};

// =====================================================
// DEVELOPMENT CONFIGURATION
// =====================================================

const DEV_CONFIG = {
  DEBUG: process.env.REACT_APP_DEBUG === 'true',
  LOG_LEVEL: process.env.REACT_APP_LOG_LEVEL || 'debug',
  DEV_TOOLS_ENABLED: process.env.REACT_APP_DEV_TOOLS_ENABLED === 'true',
  MOCK_API_ENABLED: process.env.REACT_APP_MOCK_API_ENABLED === 'true',
  HOT_RELOAD_ENABLED: process.env.REACT_APP_HOT_RELOAD_ENABLED === 'true',
};

// =====================================================
// INTERNATIONALIZATION CONFIGURATION
// =====================================================

const I18N_CONFIG = {
  ENABLED: process.env.REACT_APP_I18N_ENABLED === 'true',
  DEFAULT_LOCALE: process.env.REACT_APP_DEFAULT_LOCALE || 'en',
  SUPPORTED_LOCALES: (process.env.REACT_APP_SUPPORTED_LOCALES || 'en,es,fr,de').split(','),
  RTL_SUPPORT_ENABLED: process.env.REACT_APP_RTL_SUPPORT_ENABLED === 'true',
  NAMESPACES: ['common', 'articles', 'search', 'assessment', 'analytics'],
  FALLBACK_LOCALE: 'en',
};

// =====================================================
// ROUTES CONFIGURATION
// =====================================================

export const ARTICLE_LIBRARY_ROUTES = {
  HOME: '/articles',
  SEARCH: '/articles/search',
  RECOMMENDATIONS: '/articles/recommendations',
  FOLDERS: '/articles/folders',
  TOPICS: '/articles/topics',
  ANALYTICS: '/articles/analytics',
  ASSESSMENT: '/articles/assessment',
  SETTINGS: '/articles/settings',
  DETAIL: '/articles/:id',
  FOLDER_DETAIL: '/articles/folders/:folderId',
  TOPIC_DETAIL: '/articles/topics/:topicId',
};

// =====================================================
// NAVIGATION CONFIGURATION
// =====================================================

export const ARTICLE_LIBRARY_NAVIGATION = [
  {
    id: 'home',
    label: 'Articles',
    path: ARTICLE_LIBRARY_ROUTES.HOME,
    icon: '📚',
    description: 'Browse all articles',
  },
  {
    id: 'search',
    label: 'Search',
    path: ARTICLE_LIBRARY_ROUTES.SEARCH,
    icon: '🔍',
    description: 'Search articles',
  },
  {
    id: 'recommendations',
    label: 'Recommendations',
    path: ARTICLE_LIBRARY_ROUTES.RECOMMENDATIONS,
    icon: '⭐',
    description: 'Personalized recommendations',
    featureFlag: 'AI_RECOMMENDATIONS',
  },
  {
    id: 'folders',
    label: 'Folders',
    path: ARTICLE_LIBRARY_ROUTES.FOLDERS,
    icon: '📁',
    description: 'Organize articles in folders',
    featureFlag: 'ARTICLE_FOLDERS',
  },
  {
    id: 'topics',
    label: 'Topics',
    path: ARTICLE_LIBRARY_ROUTES.TOPICS,
    icon: '🏷️',
    description: 'Browse by topics',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    path: ARTICLE_LIBRARY_ROUTES.ANALYTICS,
    icon: '📊',
    description: 'Reading analytics and insights',
    featureFlag: 'ANALYTICS',
  },
  {
    id: 'assessment',
    label: 'Assessment',
    path: ARTICLE_LIBRARY_ROUTES.ASSESSMENT,
    icon: '📝',
    description: 'Take assessment tests',
  },
  {
    id: 'settings',
    label: 'Settings',
    path: ARTICLE_LIBRARY_ROUTES.SETTINGS,
    icon: '⚙️',
    description: 'Article library settings',
  },
];

// =====================================================
// EXPORT CONFIGURATION
// =====================================================

export const ARTICLE_LIBRARY_CONFIG = {
  API: API_CONFIG,
  FEATURES: FEATURE_FLAGS,
  UI: UI_CONFIG,
  SEARCH: SEARCH_CONFIG,
  ASSESSMENT: ASSESSMENT_CONFIG,
  CACHE: CACHE_CONFIG,
  AUTH: AUTH_CONFIG,
  SOCIAL: SOCIAL_CONFIG,
  ANALYTICS: ANALYTICS_CONFIG,
  ERROR: ERROR_CONFIG,
  DEV: DEV_CONFIG,
  I18N: I18N_CONFIG,
  ROUTES: ARTICLE_LIBRARY_ROUTES,
  NAVIGATION: ARTICLE_LIBRARY_NAVIGATION,
};

// =====================================================
// UTILITY FUNCTIONS
// =====================================================

/**
 * Check if a feature is enabled
 * @param {string} featureName - Name of the feature to check
 * @returns {boolean} - Whether the feature is enabled
 */
export const isFeatureEnabled = (featureName) => {
  return FEATURE_FLAGS[featureName] === true;
};

/**
 * Get API endpoint URL
 * @param {string} endpointName - Name of the endpoint
 * @param {string} path - Additional path
 * @returns {string} - Full API URL
 */
export const getApiUrl = (endpointName, path = '') => {
  const baseUrl = API_CONFIG.BASE_URL;
  const endpoint = API_CONFIG.ENDPOINTS[endpointName] || '';
  return `${baseUrl}${endpoint}${path}`;
};

/**
 * Get cache key for a specific resource
 * @param {string} resourceType - Type of resource
 * @param {string} identifier - Resource identifier
 * @returns {string} - Cache key
 */
export const getCacheKey = (resourceType, identifier) => {
  const cacheKey = CACHE_CONFIG.KEYS[resourceType.toUpperCase()];
  return cacheKey ? `${cacheKey}_${identifier}` : identifier;
};

/**
 * Get assessment framework configuration
 * @param {string} framework - Framework name (Be, Do, Have)
 * @returns {Object} - Framework configuration
 */
export const getFrameworkConfig = (framework) => {
  return ASSESSMENT_CONFIG.FRAMEWORKS[framework.toUpperCase()] || null;
};

/**
 * Check if user has access to content based on assessment scores
 * @param {Object} userScores - User's assessment scores
 * @param {string} framework - Framework to check
 * @param {string} level - Required level (Beginner, Intermediate, Advanced)
 * @returns {boolean} - Whether user has access
 */
export const hasContentAccess = (userScores, framework, level) => {
  if (!userScores || !userScores[framework]) return true; // Default to accessible
  
  const userScore = userScores[framework];
  const thresholds = ASSESSMENT_CONFIG.THRESHOLDS[framework.toUpperCase()];
  
  if (!thresholds) return true;
  
  switch (level.toLowerCase()) {
    case 'beginner':
      return true; // Always accessible
    case 'intermediate':
      return userScore >= thresholds.INTERMEDIATE;
    case 'advanced':
      return userScore >= thresholds.ADVANCED;
    default:
      return true;
  }
};

/**
 * Get social sharing URL
 * @param {string} platform - Social platform
 * @param {Object} params - Sharing parameters
 * @returns {string} - Sharing URL
 */
export const getSocialShareUrl = (platform, params) => {
  const platformConfig = SOCIAL_CONFIG.PLATFORMS[platform.toUpperCase()];
  if (!platformConfig || !platformConfig.ENABLED) return null;
  
  const url = new URL(platformConfig.URL);
  Object.entries(platformConfig.PARAMS).forEach(([key, value]) => {
    url.searchParams.set(key, params[key] || value);
  });
  
  return url.toString();
};

/**
 * Log analytics event
 * @param {string} eventName - Event name
 * @param {Object} properties - Event properties
 */
export const logAnalyticsEvent = (eventName, properties = {}) => {
  if (!ANALYTICS_CONFIG.ENABLED) return;
  
  // Google Analytics
  if (window.gtag && ANALYTICS_CONFIG.GOOGLE_ANALYTICS_ID) {
    window.gtag('event', eventName, properties);
  }
  
  // Mixpanel
  if (window.mixpanel && ANALYTICS_CONFIG.MIXPANEL_TOKEN) {
    window.mixpanel.track(eventName, properties);
  }
  
  // Custom analytics
  if (DEV_CONFIG.DEBUG) {
    console.log('Analytics Event:', eventName, properties);
  }
};

export default ARTICLE_LIBRARY_CONFIG;
