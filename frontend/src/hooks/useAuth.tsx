import { useState, useEffect, useCallback, createContext, useContext } from 'react';

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

interface User {
  id: string;
  email: string;
  name: string;
  isAuthenticated: boolean;
  tier?: string;
  is_beta?: boolean;
  is_admin?: boolean;
}

export interface RegisterOptions {
  beta_code?: string | null;
  /** When set without beta, server still creates budget-tier user; client may redirect to checkout. */
  selected_tier?: string | null;
  /** Explicit tier key for beta / streamlined flows (e.g. professional). */
  tier?: string | null;
  is_beta?: boolean;
  /** Vibe Checkups lead UUID for Life Ledger import after registration. */
  vc_lead_id?: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  /** JWT for Bearer APIs when present (mirrors `mingus_token` / `auth_token` storage). Cookie auth still works without this. */
  getAccessToken: () => string | null;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (
    email: string,
    password: string,
    firstName: string,
    lastName?: string,
    options?: RegisterOptions
  ) => Promise<{ isBeta: boolean }>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const getAccessToken = useCallback((): string | null => {
    try {
      return localStorage.getItem('auth_token') ?? localStorage.getItem('mingus_token');
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/verify', {
          credentials: 'include',
        });

        if (response.ok) {
          const userData = await response.json();
          if (userData.authenticated !== false && userData.user_id) {
            setUser({
              id: userData.user_id,
              email: userData.email,
              name: userData.name,
              isAuthenticated: true,
              ...(userData.tier != null && { tier: userData.tier }),
              is_beta: userData.is_beta === true,
              is_admin: userData.is_admin === true,
            });
          }
        }
      } catch (error) {
        console.error('Auth verification failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    try {
      setLoading(true);
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        credentials: 'include',
        body: JSON.stringify({ email, password, rememberMe }),
      });

      if (!response.ok) {
        let errorMessage = 'Login failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const userData: User = {
        id: data.user_id,
        email: data.email,
        name: data.name,
        isAuthenticated: true,
        ...(data.tier != null && { tier: data.tier }),
        is_beta: data.is_beta === true,
        is_admin: data.is_admin === true,
      };

      setUser(userData);
    } catch (error: unknown) {
      console.error('Login error:', error);
      if (error instanceof Error && error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check your connection.');
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (
    email: string,
    password: string,
    firstName: string,
    lastName?: string,
    options?: RegisterOptions
  ): Promise<{ isBeta: boolean }> => {
    try {
      setLoading(true);
      const betaCode = options?.beta_code?.trim() || '';
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        credentials: 'include',
        body: JSON.stringify({
          email,
          password,
          first_name: firstName,
          last_name: lastName || '',
          ...(betaCode ? { beta_code: betaCode } : {}),
          ...(options?.selected_tier ? { selected_tier: options.selected_tier } : {}),
          ...(options?.tier ? { tier: options.tier } : {}),
          ...(options?.is_beta === true ? { is_beta: true } : {}),
          ...(options?.vc_lead_id ? { vc_lead_id: options.vc_lead_id } : {}),
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Registration failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const token = data.token as string | undefined;

      if (token) {
        localStorage.setItem('auth_token', token);
      }

      let isBeta = false;
      if (betaCode && token) {
        const redeemRes = await fetch('/api/beta/redeem', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
            ...csrfHeaders(),
          },
          credentials: 'include',
          body: JSON.stringify({ code: betaCode.toUpperCase() }),
        });
        if (!redeemRes.ok) {
          let redeemErr = 'Could not activate your beta code. Please contact support.';
          try {
            const errJson = await redeemRes.json();
            redeemErr = errJson.error || errJson.message || redeemErr;
          } catch {
            /* ignore */
          }
          throw new Error(redeemErr);
        }
        isBeta = true;
      }

      const userData: User = {
        id: data.user_id,
        email: data.email,
        name: data.name || firstName,
        isAuthenticated: true,
        tier: isBeta ? 'professional' : data.tier ?? 'budget',
        is_beta: isBeta,
        is_admin: data.is_admin === true,
      };

      setUser(userData);
      return { isBeta };
    } catch (error: unknown) {
      console.error('Registration error:', error);
      if (error instanceof Error && error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to the server. Please check your connection.');
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: { ...csrfHeaders() },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user?.isAuthenticated,
    getAccessToken,
    login,
    register,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
