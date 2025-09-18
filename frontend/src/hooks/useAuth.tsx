import { useState, useEffect, createContext, useContext } from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  token: string;
  isAuthenticated: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
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

  useEffect(() => {
    // Check for existing session on mount
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('mingus_token');
        if (token) {
          // Verify token with backend
          const response = await fetch('/api/auth/verify', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const userData = await response.json();
            setUser({
              id: userData.user_id,
              email: userData.email,
              name: userData.name,
              token,
              isAuthenticated: true
            });
          } else {
            localStorage.removeItem('mingus_token');
          }
        }
      } catch (error) {
        console.error('Auth verification failed:', error);
        localStorage.removeItem('mingus_token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      const userData = {
        id: data.user_id,
        email: data.email,
        name: data.name,
        token: data.token,
        isAuthenticated: true
      };

      setUser(userData);
      localStorage.setItem('mingus_token', data.token);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('mingus_token');
  };

  const value = {
    user,
    isAuthenticated: !!user?.isAuthenticated,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
