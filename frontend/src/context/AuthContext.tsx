import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import api from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
  switchDemoUser: (email: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('edusupport_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('edusupport_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('edusupport_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('edusupport_user', JSON.stringify(res.data));
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    };
    verifyUser();
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('edusupport_token', newToken);
    localStorage.setItem('edusupport_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('edusupport_token');
    localStorage.removeItem('edusupport_user');
  };

  const switchDemoUser = async (email: string) => {
    try {
      const res = await api.post('/auth/login', {
        email,
        password: 'password123',
      });
      login(res.data.access_token, res.data.user);
    } catch (err) {
      console.error('Failed to switch user', err);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading, switchDemoUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
