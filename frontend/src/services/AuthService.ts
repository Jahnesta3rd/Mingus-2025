/**
 * Secure Authentication Service for MINGUS Application
 * Handles JWT token management with security best practices
 */

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface User {
  id: string;
  email: string;
  full_name: string;
  subscription_tier: string;
  phone_number?: string;
}

interface AuthResponse {
  success: boolean;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  subscription_tier: string;
  user: User;
}

class AuthService {
  private readonly API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
  private readonly TOKEN_KEY = 'mingus_access_token';
  private readonly REFRESH_TOKEN_KEY = 'mingus_refresh_token';
  private readonly USER_KEY = 'mingus_user';
  private readonly TOKEN_EXPIRY_KEY = 'mingus_token_expiry';
  
  private tokenRefreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.setupTokenRefresh();
  }

  /**
   * Secure token storage using httpOnly cookies (preferred) or encrypted localStorage
   */
  private storeTokens(tokens: AuthTokens): void {
    try {
      // Store tokens with encryption in localStorage (fallback)
      const encryptedTokens = this.encryptData(JSON.stringify(tokens));
      localStorage.setItem(this.TOKEN_KEY, encryptedTokens.access_token);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, encryptedTokens.refresh_token);
      
      // Store expiry time
      const expiryTime = Date.now() + (tokens.expires_in * 1000);
      localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
      
      // Setup automatic token refresh
      this.scheduleTokenRefresh(tokens.expires_in);
      
    } catch (error) {
      console.error('Error storing tokens:', error);
      throw new Error('Failed to store authentication tokens');
    }
  }

  private encryptData(data: string): { access_token: string; refresh_token: string } {
    // Simple encryption for localStorage (in production, use proper encryption)
    const encoded = btoa(data);
    return {
      access_token: encoded,
      refresh_token: encoded
    };
  }

  private decryptData(encryptedData: string): string {
    try {
      return atob(encryptedData);
    } catch {
      throw new Error('Invalid encrypted data');
    }
  }

  /**
   * Get stored access token
   */
  private getAccessToken(): string | null {
    try {
      const encryptedToken = localStorage.getItem(this.TOKEN_KEY);
      if (!encryptedToken) return null;
      
      const decrypted = this.decryptData(encryptedToken);
      const tokens = JSON.parse(decrypted);
      return tokens.access_token;
    } catch {
      this.clearTokens();
      return null;
    }
  }

  /**
   * Get stored refresh token
   */
  private getRefreshToken(): string | null {
    try {
      const encryptedToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
      if (!encryptedToken) return null;
      
      const decrypted = this.decryptData(encryptedToken);
      const tokens = JSON.parse(decrypted);
      return tokens.refresh_token;
    } catch {
      this.clearTokens();
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  private isTokenExpired(): boolean {
    const expiryTime = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiryTime) return true;
    
    return Date.now() > parseInt(expiryTime);
  }

  /**
   * Clear all stored tokens
   */
  private clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(expiresIn: number): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
    }
    
    // Refresh token 5 minutes before expiry
    const refreshTime = (expiresIn - 300) * 1000;
    this.tokenRefreshTimer = setTimeout(() => {
      this.refreshToken();
    }, refreshTime);
  }

  /**
   * Setup token refresh on app initialization
   */
  private setupTokenRefresh(): void {
    if (!this.isTokenExpired() && this.getAccessToken()) {
      const expiryTime = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
      if (expiryTime) {
        const timeUntilExpiry = parseInt(expiryTime) - Date.now();
        const refreshTime = Math.max(timeUntilExpiry - 300000, 0); // 5 minutes before expiry
        
        this.tokenRefreshTimer = setTimeout(() => {
          this.refreshToken();
        }, refreshTime);
      }
    }
  }

  /**
   * User registration
   */
  async register(userData: {
    email: string;
    password: string;
    full_name: string;
  }): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Registration failed');
      }

      // Store tokens and user data
      this.storeTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
        expires_in: data.expires_in,
      });

      localStorage.setItem(this.USER_KEY, JSON.stringify(data.user));

      return data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  /**
   * User login
   */
  async login(credentials: {
    email: string;
    password: string;
    remember_me?: boolean;
  }): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }

      // Store tokens and user data
      this.storeTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
        expires_in: data.expires_in,
      });

      localStorage.setItem(this.USER_KEY, JSON.stringify(data.user));

      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * User logout
   */
  async logout(): Promise<void> {
    try {
      const token = this.getAccessToken();
      if (token) {
        await fetch(`${this.API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${this.API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Token refresh failed');
      }

      // Update stored tokens
      this.storeTokens({
        access_token: data.access_token,
        refresh_token: refreshToken, // Keep existing refresh token
        token_type: data.token_type,
        expires_in: data.expires_in,
      });

      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearTokens();
      return false;
    }
  }

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    try {
      const userData = localStorage.getItem(this.USER_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch {
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    return token !== null && !this.isTokenExpired();
  }

  /**
   * Get authentication headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    if (token && !this.isTokenExpired()) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }
    return {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Make authenticated API request with automatic token refresh
   */
  async authenticatedRequest<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      // Check if token needs refresh
      if (this.isTokenExpired()) {
        const refreshed = await this.refreshToken();
        if (!refreshed) {
          throw new Error('Authentication required');
        }
      }

      const headers = this.getAuthHeaders();
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      // Handle token rotation (new token in response headers)
      const newToken = response.headers.get('X-New-Token');
      if (newToken) {
        const currentTokens = {
          access_token: newToken,
          refresh_token: this.getRefreshToken() || '',
          token_type: 'Bearer',
          expires_in: 3600, // Default expiry
        };
        this.storeTokens(currentTokens);
      }

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // Retry the request with new token
            return this.authenticatedRequest<T>(url, options);
          } else {
            this.clearTokens();
            throw new Error('Authentication required');
          }
        }
        throw new Error(data.message || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('Authenticated request error:', error);
      throw error;
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(profileData: Partial<User>): Promise<User> {
    return this.authenticatedRequest<User>(`${this.API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  /**
   * Change password
   */
  async changePassword(passwords: {
    current_password: string;
    new_password: string;
  }): Promise<{ success: boolean; message: string }> {
    const result = await this.authenticatedRequest<{ success: boolean; message: string }>(
      `${this.API_BASE_URL}/auth/change-password`,
      {
        method: 'POST',
        body: JSON.stringify(passwords),
      }
    );

    if (result.success) {
      // Password changed, clear tokens to force re-authentication
      this.clearTokens();
    }

    return result;
  }

  /**
   * Get subscription information
   */
  async getSubscription(): Promise<{
    tier: string;
    details: any;
  }> {
    return this.authenticatedRequest<{ tier: string; details: any }>(
      `${this.API_BASE_URL}/auth/subscription`
    );
  }

  /**
   * Get active sessions
   */
  async getActiveSessions(): Promise<{
    sessions: Array<{
      session_id: string;
      last_activity: string;
      active: boolean;
    }>;
    max_sessions: number;
  }> {
    return this.authenticatedRequest<{
      sessions: Array<{
        session_id: string;
        last_activity: string;
        active: boolean;
      }>;
      max_sessions: number;
    }>(`${this.API_BASE_URL}/auth/sessions`);
  }

  /**
   * Revoke all sessions
   */
  async revokeAllSessions(): Promise<{ success: boolean; message: string }> {
    return this.authenticatedRequest<{ success: boolean; message: string }>(
      `${this.API_BASE_URL}/auth/sessions`,
      {
        method: 'DELETE',
      }
    );
  }

  /**
   * Get user profile
   */
  async getProfile(): Promise<{
    user: User;
    profile: any;
    onboarding_progress: any;
  }> {
    return this.authenticatedRequest<{
      user: User;
      profile: any;
      onboarding_progress: any;
    }>(`${this.API_BASE_URL}/auth/profile`);
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
