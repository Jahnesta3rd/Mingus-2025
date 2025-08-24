/**
 * MINGUS API Service
 * Comprehensive API client with caching, error handling, and retry logic
 */

class APIService {
    constructor() {
        this.baseURL = config.API_BASE_URL;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        this.requestTimeout = 30000; // 30 seconds
        
        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        // Initialize
        this.setupInterceptors();
    }
    
    // ===== REQUEST/RESPONSE INTERCEPTORS =====
    setupInterceptors() {
        // Add default request interceptor for authentication
        this.addRequestInterceptor((config) => {
            const token = MINGUS.utils.Storage.get(config.TOKEN_KEY);
            if (token) {
                config.headers = config.headers || {};
                config.headers['Authorization'] = `Bearer ${token}`;
            }
            return config;
        });
        
        // Add default response interceptor for error handling
        this.addResponseInterceptor((response) => {
            return response;
        }, (error) => {
            this.handleAPIError(error);
            return Promise.reject(error);
        });
    }
    
    addRequestInterceptor(onFulfilled, onRejected) {
        this.requestInterceptors.push({ onFulfilled, onRejected });
    }
    
    addResponseInterceptor(onFulfilled, onRejected) {
        this.responseInterceptors.push({ onFulfilled, onRejected });
    }
    
    // ===== CORE HTTP METHODS =====
    async request(config) {
        try {
            // Apply request interceptors
            for (const interceptor of this.requestInterceptors) {
                config = await this.applyInterceptor(interceptor.onFulfilled, config);
            }
            
            // Create fetch request
            const response = await this.fetchWithTimeout(config);
            
            // Apply response interceptors
            for (const interceptor of this.responseInterceptors) {
                response = await this.applyInterceptor(interceptor.onFulfilled, response);
            }
            
            return response;
        } catch (error) {
            // Apply error interceptors
            for (const interceptor of this.responseInterceptors) {
                if (interceptor.onRejected) {
                    error = await this.applyInterceptor(interceptor.onRejected, error);
                }
            }
            throw error;
        }
    }
    
    async applyInterceptor(interceptor, value) {
        try {
            return await interceptor(value);
        } catch (error) {
            MINGUS.utils.logError('Interceptor error', error);
            return value;
        }
    }
    
    async fetchWithTimeout(config) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
        
        try {
            const response = await fetch(config.url, {
                method: config.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...config.headers
                },
                body: config.data ? JSON.stringify(config.data) : undefined,
                signal: controller.signal,
                credentials: 'include'
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new MINGUS.utils.AppError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    'HTTP_ERROR',
                    { status: response.status, statusText: response.statusText }
                );
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new MINGUS.utils.AppError('Request timeout', 'TIMEOUT_ERROR');
            }
            
            throw error;
        }
    }
    
    // ===== HTTP METHODS WITH RETRY LOGIC =====
    async get(url, options = {}) {
        return this.requestWithRetry(() => this.request({
            url: this.buildURL(url),
            method: 'GET',
            ...options
        }));
    }
    
    async post(url, data = null, options = {}) {
        return this.requestWithRetry(() => this.request({
            url: this.buildURL(url),
            method: 'POST',
            data,
            ...options
        }));
    }
    
    async put(url, data = null, options = {}) {
        return this.requestWithRetry(() => this.request({
            url: this.buildURL(url),
            method: 'PUT',
            data,
            ...options
        }));
    }
    
    async patch(url, data = null, options = {}) {
        return this.requestWithRetry(() => this.request({
            url: this.buildURL(url),
            method: 'PATCH',
            data,
            ...options
        }));
    }
    
    async delete(url, options = {}) {
        return this.requestWithRetry(() => this.request({
            url: this.buildURL(url),
            method: 'DELETE',
            ...options
        }));
    }
    
    // ===== RETRY LOGIC =====
    async requestWithRetry(requestFn, attempt = 1) {
        try {
            const response = await requestFn();
            return await this.parseResponse(response);
        } catch (error) {
            if (attempt < this.retryAttempts && this.shouldRetry(error)) {
                MINGUS.utils.logWarn(`Request failed, retrying... (${attempt}/${this.retryAttempts})`, error);
                await this.delay(this.retryDelay * attempt);
                return this.requestWithRetry(requestFn, attempt + 1);
            }
            throw error;
        }
    }
    
    shouldRetry(error) {
        // Retry on network errors, 5xx server errors, and 429 rate limit
        return (
            error.name === 'TypeError' || // Network error
            error.code === 'TIMEOUT_ERROR' ||
            (error.code === 'HTTP_ERROR' && 
             (error.details?.status >= 500 || error.details?.status === 429))
        );
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // ===== RESPONSE PARSING =====
    async parseResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else if (contentType && contentType.includes('text/')) {
            return await response.text();
        } else {
            return await response.blob();
        }
    }
    
    // ===== CACHING =====
    getCacheKey(url, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        return `${url}${sortedParams ? '?' + sortedParams : ''}`;
    }
    
    getCached(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }
    
    setCached(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
    
    clearCache() {
        this.cache.clear();
    }
    
    // ===== CACHED REQUESTS =====
    async getCached(url, params = {}, options = {}) {
        const cacheKey = this.getCacheKey(url, params);
        const cached = this.getCached(cacheKey);
        
        if (cached && !options.forceRefresh) {
            MINGUS.utils.logDebug('Returning cached response', { url, cacheKey });
            return cached;
        }
        
        const response = await this.get(url, { params, ...options });
        this.setCached(cacheKey, response);
        return response;
    }
    
    // ===== URL BUILDING =====
    buildURL(url, params = {}) {
        const urlObj = new URL(url, this.baseURL);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                urlObj.searchParams.append(key, value.toString());
            }
        });
        
        return urlObj.toString();
    }
    
    // ===== ERROR HANDLING =====
    handleAPIError(error) {
        MINGUS.utils.logError('API Error', error);
        
        // Handle specific error types
        switch (error.code) {
            case 'UNAUTHORIZED':
                this.handleUnauthorized();
                break;
            case 'FORBIDDEN':
                this.handleForbidden();
                break;
            case 'NOT_FOUND':
                this.handleNotFound();
                break;
            case 'RATE_LIMIT':
                this.handleRateLimit();
                break;
            case 'SERVER_ERROR':
                this.handleServerError();
                break;
            default:
                this.handleGenericError(error);
        }
    }
    
    handleUnauthorized() {
        // Clear auth data and redirect to login
        MINGUS.utils.Storage.remove(config.TOKEN_KEY);
        MINGUS.utils.Storage.remove(config.USER_KEY);
        window.location.href = '/login';
    }
    
    handleForbidden() {
        this.showNotification('Access denied. You do not have permission to perform this action.', 'error');
    }
    
    handleNotFound() {
        this.showNotification('The requested resource was not found.', 'error');
    }
    
    handleRateLimit() {
        this.showNotification('Too many requests. Please try again later.', 'warning');
    }
    
    handleServerError() {
        this.showNotification('Server error. Please try again later.', 'error');
    }
    
    handleGenericError(error) {
        this.showNotification('An unexpected error occurred. Please try again.', 'error');
    }
    
    showNotification(message, type = 'info') {
        // Dispatch custom event for notification system
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: { message, type }
        }));
    }
}

// ===== SPECIFIC API ENDPOINTS =====
class MINGUSAPI extends APIService {
    constructor() {
        super();
        this.endpoints = config.ENDPOINTS;
    }
    
    // ===== AUTHENTICATION =====
    async login(credentials) {
        return this.post(this.endpoints.AUTH.LOGIN, credentials);
    }
    
    async register(userData) {
        return this.post(this.endpoints.AUTH.REGISTER, userData);
    }
    
    async logout() {
        const response = await this.post(this.endpoints.AUTH.LOGOUT);
        MINGUS.utils.Storage.remove(config.TOKEN_KEY);
        MINGUS.utils.Storage.remove(config.USER_KEY);
        return response;
    }
    
    async refreshToken() {
        return this.post('/auth/refresh');
    }
    
    // ===== USER PROFILE =====
    async getUserProfile() {
        return this.getCached('/user/profile');
    }
    
    async updateUserProfile(profileData) {
        const response = await this.put('/user/profile', profileData);
        this.clearCache(); // Clear cache after update
        return response;
    }
    
    async deleteUserAccount() {
        return this.delete('/user/account');
    }
    
    // ===== ASSESSMENTS =====
    async getAssessments() {
        return this.getCached('/assessments');
    }
    
    async getAssessment(id) {
        return this.getCached(`/assessments/${id}`);
    }
    
    async startAssessment(assessmentId) {
        return this.post(`/assessments/${assessmentId}/start`);
    }
    
    async submitAssessment(assessmentId, answers) {
        return this.post(`/assessments/${assessmentId}/submit`, { answers });
    }
    
    async getAssessmentResults(assessmentId) {
        return this.getCached(`/assessments/${assessmentId}/results`);
    }
    
    // ===== INCOME ANALYSIS =====
    async analyzeIncome(incomeData) {
        return this.post('/income/analyze', incomeData);
    }
    
    async getIncomeComparison(currentIncome, targetIncome) {
        return this.post('/income/compare', { currentIncome, targetIncome });
    }
    
    async getIncomeRecommendations(profile) {
        return this.post('/income/recommendations', profile);
    }
    
    // ===== FINANCIAL PLANNING =====
    async createFinancialPlan(planData) {
        return this.post('/financial-plan', planData);
    }
    
    async getFinancialPlan(planId) {
        return this.getCached(`/financial-plan/${planId}`);
    }
    
    async updateFinancialPlan(planId, updates) {
        const response = await this.put(`/financial-plan/${planId}`, updates);
        this.clearCache();
        return response;
    }
    
    async deleteFinancialPlan(planId) {
        return this.delete(`/financial-plan/${planId}`);
    }
    
    // ===== ANALYTICS =====
    async getAnalytics(period = '30d') {
        return this.getCached('/analytics', { period });
    }
    
    async getDashboardData() {
        return this.getCached('/dashboard');
    }
    
    async exportData(format = 'json') {
        return this.get('/export', { params: { format } });
    }
    
    // ===== NOTIFICATIONS =====
    async getNotifications() {
        return this.getCached('/notifications');
    }
    
    async markNotificationRead(notificationId) {
        return this.patch(`/notifications/${notificationId}`, { read: true });
    }
    
    async markAllNotificationsRead() {
        return this.patch('/notifications/read-all');
    }
    
    // ===== SETTINGS =====
    async getSettings() {
        return this.getCached('/settings');
    }
    
    async updateSettings(settings) {
        const response = await this.put('/settings', settings);
        this.clearCache();
        return response;
    }
    
    // ===== FILE UPLOAD =====
    async uploadFile(file, type = 'document') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);
        
        return this.post('/upload', formData, {
            headers: {
                // Don't set Content-Type for FormData
            }
        });
    }
    
    // ===== SEARCH =====
    async search(query, filters = {}) {
        return this.get('/search', { params: { q: query, ...filters } });
    }
    
    // ===== HEALTH CHECK =====
    async healthCheck() {
        return this.get('/health');
    }
}

// ===== WEBSOCKET SUPPORT =====
class WebSocketService {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = new Map();
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                MINGUS.utils.logInfo('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('connected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.emit('message', data);
                } catch (error) {
                    MINGUS.utils.logError('Failed to parse WebSocket message', error);
                }
            };
            
            this.ws.onclose = () => {
                MINGUS.utils.logWarn('WebSocket disconnected');
                this.emit('disconnected');
                this.reconnect();
            };
            
            this.ws.onerror = (error) => {
                MINGUS.utils.logError('WebSocket error', error);
                this.emit('error', error);
            };
        } catch (error) {
            MINGUS.utils.logError('Failed to create WebSocket connection', error);
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            MINGUS.utils.logInfo(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            MINGUS.utils.logError('Max reconnection attempts reached');
            this.emit('reconnect_failed');
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            MINGUS.utils.logWarn('WebSocket is not connected');
        }
    }
    
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    MINGUS.utils.logError(`Error in WebSocket event handler for ${event}`, error);
                }
            });
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// ===== EXPORT API INSTANCES =====
const api = new MINGUSAPI();
const ws = new WebSocketService(config.WS_URL || 'ws://localhost:5000/ws');

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.api = api;
window.MINGUS.ws = ws;

// Initialize WebSocket connection
document.addEventListener('DOMContentLoaded', () => {
    if (config.WS_URL) {
        ws.connect();
    }
});
