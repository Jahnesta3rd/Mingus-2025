/**
 * MINGUS Article Library - React Context
 * =====================================
 * Context provider for article library state management and API integration
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { ARTICLE_LIBRARY_CONFIG, getApiUrl, isFeatureEnabled } from '../config/articleLibrary';

// =====================================================
// CONTEXT CREATION
// =====================================================

const ArticleLibraryContext = createContext();

// =====================================================
// INITIAL STATE
// =====================================================

const initialState = {
  // Articles state
  articles: [],
  currentArticle: null,
  articlesLoading: false,
  articlesError: null,
  
  // Search state
  searchQuery: '',
  searchResults: [],
  searchFilters: {
    categories: [],
    difficultyLevels: [],
    culturalRelevance: [],
    readingTime: [],
    publicationDate: '',
  },
  searchSortBy: 'relevance',
  searchLoading: false,
  searchError: null,
  
  // Recommendations state
  recommendations: [],
  recommendationsLoading: false,
  recommendationsError: null,
  
  // Folders state
  folders: [],
  currentFolder: null,
  foldersLoading: false,
  foldersError: null,
  
  // Topics state
  topics: [],
  currentTopic: null,
  topicsLoading: false,
  topicsError: null,
  
  // Analytics state
  analytics: {
    readingStats: {},
    preferences: {},
    progress: {},
  },
  analyticsLoading: false,
  analyticsError: null,
  
  // Assessment state
  assessmentScores: {},
  assessmentLoading: false,
  assessmentError: null,
  
  // UI state
  pagination: {
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: ARTICLE_LIBRARY_CONFIG.UI.ITEMS_PER_PAGE,
  },
  filters: {
    active: false,
    applied: {},
  },
  viewMode: 'grid', // grid, list, compact
  sortBy: 'date',
  
  // Cache state
  cache: {
    articles: new Map(),
    search: new Map(),
    recommendations: new Map(),
  },
  
  // User preferences
  preferences: {
    theme: ARTICLE_LIBRARY_CONFIG.UI.THEME,
    itemsPerPage: ARTICLE_LIBRARY_CONFIG.UI.ITEMS_PER_PAGE,
    autoRefresh: true,
    notifications: true,
  },
};

// =====================================================
// ACTION TYPES
// =====================================================

const ACTION_TYPES = {
  // Articles
  SET_ARTICLES: 'SET_ARTICLES',
  SET_CURRENT_ARTICLE: 'SET_CURRENT_ARTICLE',
  SET_ARTICLES_LOADING: 'SET_ARTICLES_LOADING',
  SET_ARTICLES_ERROR: 'SET_ARTICLES_ERROR',
  ADD_ARTICLE: 'ADD_ARTICLE',
  UPDATE_ARTICLE: 'UPDATE_ARTICLE',
  REMOVE_ARTICLE: 'REMOVE_ARTICLE',
  
  // Search
  SET_SEARCH_QUERY: 'SET_SEARCH_QUERY',
  SET_SEARCH_RESULTS: 'SET_SEARCH_RESULTS',
  SET_SEARCH_FILTERS: 'SET_SEARCH_FILTERS',
  SET_SEARCH_SORT: 'SET_SEARCH_SORT',
  SET_SEARCH_LOADING: 'SET_SEARCH_LOADING',
  SET_SEARCH_ERROR: 'SET_SEARCH_ERROR',
  CLEAR_SEARCH: 'CLEAR_SEARCH',
  
  // Recommendations
  SET_RECOMMENDATIONS: 'SET_RECOMMENDATIONS',
  SET_RECOMMENDATIONS_LOADING: 'SET_RECOMMENDATIONS_LOADING',
  SET_RECOMMENDATIONS_ERROR: 'SET_RECOMMENDATIONS_ERROR',
  
  // Folders
  SET_FOLDERS: 'SET_FOLDERS',
  SET_CURRENT_FOLDER: 'SET_CURRENT_FOLDER',
  SET_FOLDERS_LOADING: 'SET_FOLDERS_LOADING',
  SET_FOLDERS_ERROR: 'SET_FOLDERS_ERROR',
  ADD_FOLDER: 'ADD_FOLDER',
  UPDATE_FOLDER: 'UPDATE_FOLDER',
  REMOVE_FOLDER: 'REMOVE_FOLDER',
  
  // Topics
  SET_TOPICS: 'SET_TOPICS',
  SET_CURRENT_TOPIC: 'SET_CURRENT_TOPIC',
  SET_TOPICS_LOADING: 'SET_TOPICS_LOADING',
  SET_TOPICS_ERROR: 'SET_TOPICS_ERROR',
  
  // Analytics
  SET_ANALYTICS: 'SET_ANALYTICS',
  SET_ANALYTICS_LOADING: 'SET_ANALYTICS_LOADING',
  SET_ANALYTICS_ERROR: 'SET_ANALYTICS_ERROR',
  
  // Assessment
  SET_ASSESSMENT_SCORES: 'SET_ASSESSMENT_SCORES',
  SET_ASSESSMENT_LOADING: 'SET_ASSESSMENT_LOADING',
  SET_ASSESSMENT_ERROR: 'SET_ASSESSMENT_ERROR',
  
  // UI
  SET_PAGINATION: 'SET_PAGINATION',
  SET_FILTERS: 'SET_FILTERS',
  SET_VIEW_MODE: 'SET_VIEW_MODE',
  SET_SORT_BY: 'SET_SORT_BY',
  
  // Cache
  SET_CACHE_ITEM: 'SET_CACHE_ITEM',
  CLEAR_CACHE: 'CLEAR_CACHE',
  
  // Preferences
  SET_PREFERENCES: 'SET_PREFERENCES',
  
  // Reset
  RESET_STATE: 'RESET_STATE',
};

// =====================================================
// REDUCER
// =====================================================

const articleLibraryReducer = (state, action) => {
  switch (action.type) {
    // Articles
    case ACTION_TYPES.SET_ARTICLES:
      return {
        ...state,
        articles: action.payload,
        articlesError: null,
      };
      
    case ACTION_TYPES.SET_CURRENT_ARTICLE:
      return {
        ...state,
        currentArticle: action.payload,
      };
      
    case ACTION_TYPES.SET_ARTICLES_LOADING:
      return {
        ...state,
        articlesLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_ARTICLES_ERROR:
      return {
        ...state,
        articlesError: action.payload,
        articlesLoading: false,
      };
      
    case ACTION_TYPES.ADD_ARTICLE:
      return {
        ...state,
        articles: [action.payload, ...state.articles],
      };
      
    case ACTION_TYPES.UPDATE_ARTICLE:
      return {
        ...state,
        articles: state.articles.map(article =>
          article.id === action.payload.id ? action.payload : article
        ),
        currentArticle: state.currentArticle?.id === action.payload.id 
          ? action.payload 
          : state.currentArticle,
      };
      
    case ACTION_TYPES.REMOVE_ARTICLE:
      return {
        ...state,
        articles: state.articles.filter(article => article.id !== action.payload),
        currentArticle: state.currentArticle?.id === action.payload 
          ? null 
          : state.currentArticle,
      };
      
    // Search
    case ACTION_TYPES.SET_SEARCH_QUERY:
      return {
        ...state,
        searchQuery: action.payload,
      };
      
    case ACTION_TYPES.SET_SEARCH_RESULTS:
      return {
        ...state,
        searchResults: action.payload,
        searchError: null,
      };
      
    case ACTION_TYPES.SET_SEARCH_FILTERS:
      return {
        ...state,
        searchFilters: { ...state.searchFilters, ...action.payload },
      };
      
    case ACTION_TYPES.SET_SEARCH_SORT:
      return {
        ...state,
        searchSortBy: action.payload,
      };
      
    case ACTION_TYPES.SET_SEARCH_LOADING:
      return {
        ...state,
        searchLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_SEARCH_ERROR:
      return {
        ...state,
        searchError: action.payload,
        searchLoading: false,
      };
      
    case ACTION_TYPES.CLEAR_SEARCH:
      return {
        ...state,
        searchQuery: '',
        searchResults: [],
        searchFilters: initialState.searchFilters,
        searchError: null,
      };
      
    // Recommendations
    case ACTION_TYPES.SET_RECOMMENDATIONS:
      return {
        ...state,
        recommendations: action.payload,
        recommendationsError: null,
      };
      
    case ACTION_TYPES.SET_RECOMMENDATIONS_LOADING:
      return {
        ...state,
        recommendationsLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_RECOMMENDATIONS_ERROR:
      return {
        ...state,
        recommendationsError: action.payload,
        recommendationsLoading: false,
      };
      
    // Folders
    case ACTION_TYPES.SET_FOLDERS:
      return {
        ...state,
        folders: action.payload,
        foldersError: null,
      };
      
    case ACTION_TYPES.SET_CURRENT_FOLDER:
      return {
        ...state,
        currentFolder: action.payload,
      };
      
    case ACTION_TYPES.SET_FOLDERS_LOADING:
      return {
        ...state,
        foldersLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_FOLDERS_ERROR:
      return {
        ...state,
        foldersError: action.payload,
        foldersLoading: false,
      };
      
    case ACTION_TYPES.ADD_FOLDER:
      return {
        ...state,
        folders: [...state.folders, action.payload],
      };
      
    case ACTION_TYPES.UPDATE_FOLDER:
      return {
        ...state,
        folders: state.folders.map(folder =>
          folder.id === action.payload.id ? action.payload : folder
        ),
        currentFolder: state.currentFolder?.id === action.payload.id 
          ? action.payload 
          : state.currentFolder,
      };
      
    case ACTION_TYPES.REMOVE_FOLDER:
      return {
        ...state,
        folders: state.folders.filter(folder => folder.id !== action.payload),
        currentFolder: state.currentFolder?.id === action.payload 
          ? null 
          : state.currentFolder,
      };
      
    // Topics
    case ACTION_TYPES.SET_TOPICS:
      return {
        ...state,
        topics: action.payload,
        topicsError: null,
      };
      
    case ACTION_TYPES.SET_CURRENT_TOPIC:
      return {
        ...state,
        currentTopic: action.payload,
      };
      
    case ACTION_TYPES.SET_TOPICS_LOADING:
      return {
        ...state,
        topicsLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_TOPICS_ERROR:
      return {
        ...state,
        topicsError: action.payload,
        topicsLoading: false,
      };
      
    // Analytics
    case ACTION_TYPES.SET_ANALYTICS:
      return {
        ...state,
        analytics: action.payload,
        analyticsError: null,
      };
      
    case ACTION_TYPES.SET_ANALYTICS_LOADING:
      return {
        ...state,
        analyticsLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_ANALYTICS_ERROR:
      return {
        ...state,
        analyticsError: action.payload,
        analyticsLoading: false,
      };
      
    // Assessment
    case ACTION_TYPES.SET_ASSESSMENT_SCORES:
      return {
        ...state,
        assessmentScores: action.payload,
        assessmentError: null,
      };
      
    case ACTION_TYPES.SET_ASSESSMENT_LOADING:
      return {
        ...state,
        assessmentLoading: action.payload,
      };
      
    case ACTION_TYPES.SET_ASSESSMENT_ERROR:
      return {
        ...state,
        assessmentError: action.payload,
        assessmentLoading: false,
      };
      
    // UI
    case ACTION_TYPES.SET_PAGINATION:
      return {
        ...state,
        pagination: { ...state.pagination, ...action.payload },
      };
      
    case ACTION_TYPES.SET_FILTERS:
      return {
        ...state,
        filters: { ...state.filters, ...action.payload },
      };
      
    case ACTION_TYPES.SET_VIEW_MODE:
      return {
        ...state,
        viewMode: action.payload,
      };
      
    case ACTION_TYPES.SET_SORT_BY:
      return {
        ...state,
        sortBy: action.payload,
      };
      
    // Cache
    case ACTION_TYPES.SET_CACHE_ITEM:
      const { key, value, type } = action.payload;
      return {
        ...state,
        cache: {
          ...state.cache,
          [type]: new Map(state.cache[type]).set(key, value),
        },
      };
      
    case ACTION_TYPES.CLEAR_CACHE:
      return {
        ...state,
        cache: initialState.cache,
      };
      
    // Preferences
    case ACTION_TYPES.SET_PREFERENCES:
      return {
        ...state,
        preferences: { ...state.preferences, ...action.payload },
      };
      
    // Reset
    case ACTION_TYPES.RESET_STATE:
      return initialState;
      
    default:
      return state;
  }
};

// =====================================================
// API FUNCTIONS
// =====================================================

const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem(ARTICLE_LIBRARY_CONFIG.AUTH.JWT_STORAGE_KEY);
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    timeout: ARTICLE_LIBRARY_CONFIG.API.TIMEOUT,
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
};

// =====================================================
// CONTEXT PROVIDER
// =====================================================

export const ArticleLibraryProvider = ({ children }) => {
  const [state, dispatch] = useReducer(articleLibraryReducer, initialState);

  // =====================================================
  // ARTICLES ACTIONS
  // =====================================================

  const fetchArticles = useCallback(async (params = {}) => {
    try {
      dispatch({ type: ACTION_TYPES.SET_ARTICLES_LOADING, payload: true });
      
      const queryParams = new URLSearchParams({
        page: params.page || 1,
        per_page: params.per_page || state.pagination.itemsPerPage,
        sort_by: params.sortBy || state.sortBy,
        ...params,
      });
      
      const url = `${getApiUrl('ARTICLES')}?${queryParams}`;
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_ARTICLES, payload: data.articles });
      dispatch({ type: ACTION_TYPES.SET_PAGINATION, payload: {
        currentPage: data.pagination.current_page,
        totalPages: data.pagination.total_pages,
        totalItems: data.pagination.total_items,
      }});
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_ARTICLES_ERROR, payload: error.message });
    }
  }, [state.pagination.itemsPerPage, state.sortBy]);

  const fetchArticleById = useCallback(async (id) => {
    try {
      dispatch({ type: ACTION_TYPES.SET_ARTICLES_LOADING, payload: true });
      
      const url = getApiUrl('ARTICLES', `/${id}`);
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_CURRENT_ARTICLE, payload: data });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_ARTICLES_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // SEARCH ACTIONS
  // =====================================================

  const searchArticles = useCallback(async (query, filters = {}) => {
    try {
      dispatch({ type: ACTION_TYPES.SET_SEARCH_LOADING, payload: true });
      
      const searchParams = {
        q: query,
        ...filters,
        sort_by: state.searchSortBy,
      };
      
      const queryParams = new URLSearchParams(searchParams);
      const url = `${getApiUrl('SEARCH')}?${queryParams}`;
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_SEARCH_RESULTS, payload: data.results });
      dispatch({ type: ACTION_TYPES.SET_SEARCH_QUERY, payload: query });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_SEARCH_ERROR, payload: error.message });
    }
  }, [state.searchSortBy]);

  // =====================================================
  // RECOMMENDATIONS ACTIONS
  // =====================================================

  const fetchRecommendations = useCallback(async (limit = 20) => {
    if (!isFeatureEnabled('AI_RECOMMENDATIONS')) return;
    
    try {
      dispatch({ type: ACTION_TYPES.SET_RECOMMENDATIONS_LOADING, payload: true });
      
      const url = `${getApiUrl('RECOMMENDATIONS')}?limit=${limit}`;
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_RECOMMENDATIONS, payload: data.recommendations });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_RECOMMENDATIONS_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // FOLDERS ACTIONS
  // =====================================================

  const fetchFolders = useCallback(async () => {
    if (!isFeatureEnabled('ARTICLE_FOLDERS')) return;
    
    try {
      dispatch({ type: ACTION_TYPES.SET_FOLDERS_LOADING, payload: true });
      
      const url = getApiUrl('FOLDERS');
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_FOLDERS, payload: data.folders });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_FOLDERS_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // TOPICS ACTIONS
  // =====================================================

  const fetchTopics = useCallback(async () => {
    try {
      dispatch({ type: ACTION_TYPES.SET_TOPICS_LOADING, payload: true });
      
      const url = getApiUrl('TOPICS');
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_TOPICS, payload: data.topics });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_TOPICS_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // ANALYTICS ACTIONS
  // =====================================================

  const fetchAnalytics = useCallback(async () => {
    if (!isFeatureEnabled('ANALYTICS')) return;
    
    try {
      dispatch({ type: ACTION_TYPES.SET_ANALYTICS_LOADING, payload: true });
      
      const url = getApiUrl('ANALYTICS');
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_ANALYTICS, payload: data });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_ANALYTICS_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // ASSESSMENT ACTIONS
  // =====================================================

  const fetchAssessmentScores = useCallback(async () => {
    try {
      dispatch({ type: ACTION_TYPES.SET_ASSESSMENT_LOADING, payload: true });
      
      const url = `${getApiUrl('AUTH')}/assessment-scores`;
      const data = await apiCall(url);
      
      dispatch({ type: ACTION_TYPES.SET_ASSESSMENT_SCORES, payload: data.scores });
      
    } catch (error) {
      dispatch({ type: ACTION_TYPES.SET_ASSESSMENT_ERROR, payload: error.message });
    }
  }, []);

  // =====================================================
  // CACHE ACTIONS
  // =====================================================

  const setCacheItem = useCallback((key, value, type = 'articles') => {
    dispatch({
      type: ACTION_TYPES.SET_CACHE_ITEM,
      payload: { key, value, type },
    });
  }, []);

  const getCacheItem = useCallback((key, type = 'articles') => {
    return state.cache[type].get(key);
  }, [state.cache]);

  const clearCache = useCallback(() => {
    dispatch({ type: ACTION_TYPES.CLEAR_CACHE });
  }, []);

  // =====================================================
  // UI ACTIONS
  // =====================================================

  const setViewMode = useCallback((mode) => {
    dispatch({ type: ACTION_TYPES.SET_VIEW_MODE, payload: mode });
  }, []);

  const setSortBy = useCallback((sortBy) => {
    dispatch({ type: ACTION_TYPES.SET_SORT_BY, payload: sortBy });
  }, []);

  const setFilters = useCallback((filters) => {
    dispatch({ type: ACTION_TYPES.SET_FILTERS, payload: filters });
  }, []);

  const setPreferences = useCallback((preferences) => {
    dispatch({ type: ACTION_TYPES.SET_PREFERENCES, payload: preferences });
  }, []);

  // =====================================================
  // UTILITY ACTIONS
  // =====================================================

  const clearSearch = useCallback(() => {
    dispatch({ type: ACTION_TYPES.CLEAR_SEARCH });
  }, []);

  const resetState = useCallback(() => {
    dispatch({ type: ACTION_TYPES.RESET_STATE });
  }, []);

  // =====================================================
  // EFFECTS
  // =====================================================

  useEffect(() => {
    // Load initial data
    fetchArticles();
    fetchTopics();
    
    if (isFeatureEnabled('AI_RECOMMENDATIONS')) {
      fetchRecommendations();
    }
    
    if (isFeatureEnabled('ARTICLE_FOLDERS')) {
      fetchFolders();
    }
    
    if (isFeatureEnabled('ANALYTICS')) {
      fetchAnalytics();
    }
    
    fetchAssessmentScores();
  }, []);

  // =====================================================
  // CONTEXT VALUE
  // =====================================================

  const contextValue = {
    // State
    ...state,
    
    // Actions
    fetchArticles,
    fetchArticleById,
    searchArticles,
    fetchRecommendations,
    fetchFolders,
    fetchTopics,
    fetchAnalytics,
    fetchAssessmentScores,
    
    // Cache
    setCacheItem,
    getCacheItem,
    clearCache,
    
    // UI
    setViewMode,
    setSortBy,
    setFilters,
    setPreferences,
    
    // Utilities
    clearSearch,
    resetState,
  };

  return (
    <ArticleLibraryContext.Provider value={contextValue}>
      {children}
    </ArticleLibraryContext.Provider>
  );
};

// =====================================================
// HOOK
// =====================================================

export const useArticleLibrary = () => {
  const context = useContext(ArticleLibraryContext);
  
  if (!context) {
    throw new Error('useArticleLibrary must be used within an ArticleLibraryProvider');
  }
  
  return context;
};

// =====================================================
// EXPORTS
// =====================================================

export { ACTION_TYPES };
export default ArticleLibraryContext;
