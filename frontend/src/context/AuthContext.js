import React, { createContext, useState, useContext, useEffect } from 'react';
import * as api from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = api.getAuthToken();

    if (!token) {
      setLoading(false);
      setIsAuthenticated(false);
      setUser(null);
      return;
    }

    try {
      const userData = await api.get('/auth/me');
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check failed:', error);
      api.clearAuthToken();
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const data = await api.post('/auth/login', { email, password });
      api.setAuthToken(data.token);
      setUser(data.user);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { success: false, error: error.message };
    }
  };

  const register = async (email, password, fullName) => {
    try {
      const data = await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
      });
      api.setAuthToken(data.token);
      setUser(data.user);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      console.error('Registration failed:', error);
      return { success: false, error: error.message };
    }
  };

  const loginWithGoogle = () => {
    // Redirect to Google OAuth on the backend server
    // Note: window.location redirects bypass the proxy, so we need the full URL
    window.location.href = 'http://localhost:5000/auth/google/login';
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      api.clearAuthToken();
      setUser(null);
      setIsAuthenticated(false);
      window.location.href = '/login';
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
