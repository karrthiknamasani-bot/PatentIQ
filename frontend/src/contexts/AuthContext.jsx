import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      setUser(data.data);
      localStorage.setItem('token', data.data.token);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || 'Login failed',
        unverified: error.response?.data?.unverified || false
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/register', { name, email, password });
      // We do not set user here because they need to verify email
      return { success: true, message: data.message };
    } catch (error) {
      return { success: false, message: error.response?.data?.message || 'Registration failed' };
    } finally {
      setLoading(false);
    }
  };

  const verifyEmailOTP = async (email, otp) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/verify-email-otp', { email, otp });
      return data;
    } catch (error) {
      return { success: false, message: error.response?.data?.message || 'Verification failed' };
    } finally {
      setLoading(false);
    }
  };

  const resendEmailVerificationOTP = async (email) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/resend-verification-otp', { email });
      return data;
    } catch (error) {
      return { success: false, message: error.response?.data?.message || 'Failed to resend verification' };
    } finally {
      setLoading(false);
    }
  };


  const googleLogin = async (idToken) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/google', { idToken });
      
      if (data.success) {
        localStorage.setItem('token', data.data.token);
        setUser(data.data);
      }
      return data;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Google authentication failed'
      };
    } finally {
      setLoading(false);
    }
  };

  // Forgot Password
  const forgotPassword = async (email) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/forgot-password', { email });
      return data;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to send reset email'
      };
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP
  const verifyOTP = async (email, otp) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/verify-otp', { email, otp });
      return data;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to verify OTP'
      };
    } finally {
      setLoading(false);
    }
  };

  // Reset Password
  const resetPassword = async (email, otp, newPassword) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/reset-password', { email, otp, newPassword });
      
      // Auto-login after reset password
      if (data.success) {
        localStorage.setItem('token', data.data.token);
        setUser(data.data);
      }
      return data;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to reset password'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      login, 
      register, 
      googleLogin, 
      forgotPassword,
      verifyOTP,
      resetPassword,
      verifyEmailOTP,
      resendEmailVerificationOTP,
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
