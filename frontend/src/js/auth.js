/**
 * MINGUS Authentication Service
 * Comprehensive authentication with JWT handling, session management, and security features
 */

class AuthService {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.tokenRefreshTimer = null;
        this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
        this.sessionTimer = null;
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        // Check for existing session
        this.checkExistingSession();
        
        // Setup session timeout
        this.setupSessionTimeout();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup token refresh
        this.setupTokenRefresh();
    }
    
    checkExistingSession() {
        const token = MINGUS.utils.Storage.get(config.TOKEN_KEY);
        const user = MINGUS.utils.Storage.get(config.USER_KEY);
        
        if (token && user) {
            // Validate token
            if (this.isTokenValid(token)) {
                this.currentUser = user;
                this.isAuthenticated = true;
                this.updateUI();
                MINGUS.utils.logInfo('Session restored', { user: user.email });
            } else {
                this.clearSession();
                MINGUS.utils.logWarn('Invalid token found, session cleared');
            }
        }
    }
    
    setupSessionTimeout() {
        // Reset session timer on user activity
        const resetSessionTimer = MINGUS.utils.Performance.debounce(() => {
            this.resetSessionTimer();
        }, 1000);
        
        // Listen for user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetSessionTimer, true);
        });
    }
    
    setupEventListeners() {
        // Listen for storage changes (other tabs)
        window.addEventListener('storage', (event) => {
            if (event.key === config.TOKEN_KEY || event.key === config.USER_KEY) {
                this.handleStorageChange(event);
            }
        });
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.checkSessionValidity();
            }
        });
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.handleOffline();
        });
    }
    
    setupTokenRefresh() {
        // Refresh token every 15 minutes
        setInterval(() => {
            if (this.isAuthenticated) {
                this.refreshToken();
            }
        }, 15 * 60 * 1000);
    }
    
    // ===== AUTHENTICATION METHODS =====
    async login(credentials) {
        try {
            MINGUS.utils.logInfo('Attempting login', { email: credentials.email });
            
            // Validate credentials
            if (!this.validateCredentials(credentials)) {
                throw new MINGUS.utils.AppError('Invalid credentials', 'VALIDATION_ERROR');
            }
            
            // Show loading state
            this.showLoadingState();
            
            // Make API request
            const response = await MINGUS.api.login(credentials);
            
            // Process response
            if (response.success && response.data) {
                await this.handleLoginSuccess(response.data);
                return response;
            } else {
                throw new MINGUS.utils.AppError(response.message || 'Login failed', 'LOGIN_ERROR');
            }
        } catch (error) {
            MINGUS.utils.logError('Login failed', error);
            this.handleLoginError(error);
            throw error;
        } finally {
            this.hideLoadingState();
        }
    }
    
    async register(userData) {
        try {
            MINGUS.utils.logInfo('Attempting registration', { email: userData.email });
            
            // Validate user data
            if (!this.validateRegistrationData(userData)) {
                throw new MINGUS.utils.AppError('Invalid registration data', 'VALIDATION_ERROR');
            }
            
            // Show loading state
            this.showLoadingState();
            
            // Make API request
            const response = await MINGUS.api.register(userData);
            
            // Process response
            if (response.success && response.data) {
                await this.handleRegistrationSuccess(response.data);
                return response;
            } else {
                throw new MINGUS.utils.AppError(response.message || 'Registration failed', 'REGISTRATION_ERROR');
            }
        } catch (error) {
            MINGUS.utils.logError('Registration failed', error);
            this.handleRegistrationError(error);
            throw error;
        } finally {
            this.hideLoadingState();
        }
    }
    
    async logout() {
        try {
            MINGUS.utils.logInfo('Logging out');
            
            // Call logout API
            if (this.isAuthenticated) {
                await MINGUS.api.logout();
            }
        } catch (error) {
            MINGUS.utils.logError('Logout API call failed', error);
        } finally {
            // Always clear local session
            this.clearSession();
            this.redirectToLogin();
        }
    }
    
    async refreshToken() {
        try {
            const token = MINGUS.utils.Storage.get(config.TOKEN_KEY);
            if (!token) {
                throw new MINGUS.utils.AppError('No token to refresh', 'NO_TOKEN');
            }
            
            const response = await MINGUS.api.refreshToken();
            
            if (response.success && response.data?.token) {
                this.setToken(response.data.token);
                MINGUS.utils.logInfo('Token refreshed successfully');
            } else {
                throw new MINGUS.utils.AppError('Token refresh failed', 'REFRESH_ERROR');
            }
        } catch (error) {
            MINGUS.utils.logError('Token refresh failed', error);
            // If refresh fails, logout user
            await this.logout();
        }
    }
    
    // ===== SESSION MANAGEMENT =====
    setToken(token) {
        MINGUS.utils.Storage.set(config.TOKEN_KEY, token);
        this.resetSessionTimer();
    }
    
    getToken() {
        return MINGUS.utils.Storage.get(config.TOKEN_KEY);
    }
    
    isTokenValid(token) {
        if (!token) return false;
        
        try {
            const payload = this.decodeToken(token);
            const now = Date.now() / 1000;
            
            // Check if token is expired
            if (payload.exp && payload.exp < now) {
                return false;
            }
            
            // Check if token is not yet valid
            if (payload.nbf && payload.nbf > now) {
                return false;
            }
            
            return true;
        } catch (error) {
            MINGUS.utils.logError('Token validation failed', error);
            return false;
        }
    }
    
    decodeToken(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            return JSON.parse(jsonPayload);
        } catch (error) {
            MINGUS.utils.logError('Token decoding failed', error);
            throw new MINGUS.utils.AppError('Invalid token format', 'INVALID_TOKEN');
        }
    }
    
    resetSessionTimer() {
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
        }
        
        this.sessionTimer = setTimeout(() => {
            this.handleSessionTimeout();
        }, this.sessionTimeout);
    }
    
    handleSessionTimeout() {
        MINGUS.utils.logWarn('Session timeout');
        this.showSessionTimeoutWarning();
    }
    
    // ===== SUCCESS HANDLERS =====
    async handleLoginSuccess(data) {
        // Set token and user data
        this.setToken(data.token);
        this.currentUser = data.user;
        this.isAuthenticated = true;
        
        // Store user data
        MINGUS.utils.Storage.set(config.USER_KEY, data.user);
        
        // Update UI
        this.updateUI();
        
        // Track analytics
        this.trackAuthEvent('login', data.user);
        
        // Redirect to dashboard
        this.redirectToDashboard();
        
        MINGUS.utils.logInfo('Login successful', { user: data.user.email });
    }
    
    async handleRegistrationSuccess(data) {
        // Set token and user data
        this.setToken(data.token);
        this.currentUser = data.user;
        this.isAuthenticated = true;
        
        // Store user data
        MINGUS.utils.Storage.set(config.USER_KEY, data.user);
        
        // Update UI
        this.updateUI();
        
        // Track analytics
        this.trackAuthEvent('register', data.user);
        
        // Redirect to onboarding
        this.redirectToOnboarding();
        
        MINGUS.utils.logInfo('Registration successful', { user: data.user.email });
    }
    
    // ===== ERROR HANDLERS =====
    handleLoginError(error) {
        let message = 'Login failed. Please try again.';
        
        switch (error.code) {
            case 'INVALID_CREDENTIALS':
                message = 'Invalid email or password.';
                break;
            case 'ACCOUNT_LOCKED':
                message = 'Account is locked. Please contact support.';
                break;
            case 'ACCOUNT_DISABLED':
                message = 'Account is disabled. Please contact support.';
                break;
            case 'NETWORK_ERROR':
                message = 'Network error. Please check your connection.';
                break;
        }
        
        this.showError(message);
    }
    
    handleRegistrationError(error) {
        let message = 'Registration failed. Please try again.';
        
        switch (error.code) {
            case 'EMAIL_EXISTS':
                message = 'An account with this email already exists.';
                break;
            case 'WEAK_PASSWORD':
                message = 'Password is too weak. Please choose a stronger password.';
                break;
            case 'INVALID_EMAIL':
                message = 'Please enter a valid email address.';
                break;
            case 'NETWORK_ERROR':
                message = 'Network error. Please check your connection.';
                break;
        }
        
        this.showError(message);
    }
    
    // ===== VALIDATION =====
    validateCredentials(credentials) {
        if (!credentials.email || !credentials.password) {
            return false;
        }
        
        if (!MINGUS.utils.Validation.isEmail(credentials.email)) {
            return false;
        }
        
        if (credentials.password.length < 8) {
            return false;
        }
        
        return true;
    }
    
    validateRegistrationData(userData) {
        if (!userData.email || !userData.password || !userData.confirmPassword) {
            return false;
        }
        
        if (!MINGUS.utils.Validation.isEmail(userData.email)) {
            return false;
        }
        
        if (userData.password.length < 8) {
            return false;
        }
        
        if (userData.password !== userData.confirmPassword) {
            return false;
        }
        
        if (userData.firstName && userData.firstName.length < 2) {
            return false;
        }
        
        if (userData.lastName && userData.lastName.length < 2) {
            return false;
        }
        
        return true;
    }
    
    // ===== UI UPDATES =====
    updateUI() {
        const usernameElement = document.getElementById('username');
        const loginBtn = document.getElementById('loginBtn');
        
        if (this.isAuthenticated && this.currentUser) {
            if (usernameElement) {
                usernameElement.textContent = this.currentUser.firstName || this.currentUser.email;
            }
            
            if (loginBtn) {
                loginBtn.textContent = 'Logout';
                loginBtn.onclick = () => this.logout();
            }
        } else {
            if (usernameElement) {
                usernameElement.textContent = 'Guest';
            }
            
            if (loginBtn) {
                loginBtn.textContent = 'Login';
                loginBtn.onclick = () => this.showLoginModal();
            }
        }
    }
    
    showLoadingState() {
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.disabled = true;
            loginBtn.textContent = 'Loading...';
        }
    }
    
    hideLoadingState() {
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.disabled = false;
            this.updateUI();
        }
    }
    
    showError(message) {
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: { message, type: 'error' }
        }));
    }
    
    showSessionTimeoutWarning() {
        const message = 'Your session will expire soon. Click here to extend your session.';
        const notification = {
            message,
            type: 'warning',
            action: {
                label: 'Extend Session',
                handler: () => this.extendSession()
            }
        };
        
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: notification
        }));
    }
    
    // ===== SESSION EXTENSION =====
    async extendSession() {
        try {
            await this.refreshToken();
            this.resetSessionTimer();
            
            window.dispatchEvent(new CustomEvent('showNotification', {
                detail: { message: 'Session extended successfully', type: 'success' }
            }));
        } catch (error) {
            MINGUS.utils.logError('Session extension failed', error);
            await this.logout();
        }
    }
    
    // ===== EVENT HANDLERS =====
    handleStorageChange(event) {
        if (event.newValue === null) {
            // Token or user data was cleared in another tab
            this.clearSession();
            this.redirectToLogin();
        }
    }
    
    async checkSessionValidity() {
        if (this.isAuthenticated) {
            const token = this.getToken();
            if (!this.isTokenValid(token)) {
                MINGUS.utils.logWarn('Session expired');
                await this.logout();
            }
        }
    }
    
    handleOnline() {
        MINGUS.utils.logInfo('Connection restored');
        this.checkSessionValidity();
    }
    
    handleOffline() {
        MINGUS.utils.logWarn('Connection lost');
    }
    
    // ===== UTILITY METHODS =====
    clearSession() {
        this.currentUser = null;
        this.isAuthenticated = false;
        
        // Clear storage
        MINGUS.utils.Storage.remove(config.TOKEN_KEY);
        MINGUS.utils.Storage.remove(config.USER_KEY);
        
        // Clear timers
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
            this.sessionTimer = null;
        }
        
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
            this.tokenRefreshTimer = null;
        }
        
        // Update UI
        this.updateUI();
        
        MINGUS.utils.logInfo('Session cleared');
    }
    
    redirectToLogin() {
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    }
    
    redirectToDashboard() {
        window.location.href = '/dashboard';
    }
    
    redirectToOnboarding() {
        window.location.href = '/onboarding';
    }
    
    showLoginModal() {
        // Dispatch event to show login modal
        window.dispatchEvent(new CustomEvent('showLoginModal'));
    }
    
    trackAuthEvent(action, user) {
        if (window.analytics && window.analytics.track) {
            window.analytics.track('auth_event', {
                action,
                user_id: user.id,
                email: user.email
            });
        }
    }
    
    // ===== PUBLIC API =====
    getCurrentUser() {
        return this.currentUser;
    }
    
    isLoggedIn() {
        return this.isAuthenticated && this.currentUser !== null;
    }
    
    hasPermission(permission) {
        if (!this.isAuthenticated || !this.currentUser) {
            return false;
        }
        
        return this.currentUser.permissions?.includes(permission) || false;
    }
    
    hasRole(role) {
        if (!this.isAuthenticated || !this.currentUser) {
            return false;
        }
        
        return this.currentUser.roles?.includes(role) || false;
    }
}

// ===== EXPORT AUTH SERVICE =====
const auth = new AuthService();

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.auth = auth;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthService;
}
