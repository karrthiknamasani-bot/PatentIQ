import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '../api/supabase';

const DEMO_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  name: 'Demo Innovator',
  email: 'demo.innovator@patentiq.local',
  token: 'patentiq-dev-demo-token-00000000-0000-0000-0000-000000000001',
  isDemo: true,
};

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for authenticated Google or local session first
    const storedAuth = localStorage.getItem('patentiq_session');
    if (storedAuth) {
      try {
        setUser(JSON.parse(storedAuth));
        setLoading(false);
        return;
      } catch (e) {
        localStorage.removeItem('patentiq_session');
      }
    }

    if (!isSupabaseConfigured || !supabase) {
      // Check for persisted demo session
      const stored = localStorage.getItem('patentiq_demo_session');
      if (stored) {
        try {
          setUser(JSON.parse(stored));
        } catch (e) {
          localStorage.removeItem('patentiq_demo_session');
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
      return;
    }

    // Check active Supabase session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser({
          id: session.user.id,
          name: session.user.user_metadata?.name || session.user.email.split('@')[0],
          email: session.user.email,
          token: session.access_token,
          avatar: session.user.user_metadata?.avatar_url || null,
          isDemo: false,
        });
      } else {
        setUser(null);
      }
      setLoading(false);
    }).catch(() => {
      setUser(null);
      setLoading(false);
    });

    // Listen for Supabase auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser({
          id: session.user.id,
          name: session.user.user_metadata?.name || session.user.email.split('@')[0],
          email: session.user.email,
          token: session.access_token,
          avatar: session.user.user_metadata?.avatar_url || null,
          isDemo: false,
        });
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => subscription?.unsubscribe?.();
  }, []);

  const loginDemo = () => {
    localStorage.setItem('patentiq_demo_session', JSON.stringify(DEMO_USER));
    setUser(DEMO_USER);
    return { success: true, message: 'Logged in as Demo Innovator' };
  };

  const login = async (email, password) => {
    if (!isSupabaseConfigured || !supabase) {
      return {
        success: false,
        message: 'Supabase is not configured. Please use Demo Mode.',
      };
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return { success: true };
    } catch (error) {
      return {
        success: false,
        message: error.message || 'Login failed',
      };
    } finally {
      setLoading(false);
    }
  };

  const googleLogin = async (credential) => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
      const res = await fetch(`${apiBase}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ credential }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Google authentication failed.');
      }

      const data = await res.json();
      const sessionUser = {
        id: data.user.id,
        name: data.user.name || data.user.email.split('@')[0],
        email: data.user.email,
        token: data.access_token,
        avatar: data.user.avatar || null,
        isDemo: false,
      };

      localStorage.setItem('patentiq_session', JSON.stringify(sessionUser));
      setUser(sessionUser);
      return { success: true };
    } catch (error) {
      if (isSupabaseConfigured && supabase) {
        try {
          const { error: sbError } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
              redirectTo: window.location.origin,
            },
          });
          if (sbError) throw sbError;
          return { success: true };
        } catch (sbErr) {
          return {
            success: false,
            message: sbErr.message || 'Google login failed',
          };
        }
      }
      return {
        success: false,
        message: error.message || 'Google login failed',
      };
    }
  };

  const register = async (name, email, password) => {
    if (!isSupabaseConfigured || !supabase) {
      return {
        success: false,
        message: 'Supabase is not configured. Please use Demo Mode.',
      };
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { name },
        },
      });
      if (error) throw error;
      return { success: true, message: 'Registration successful! Please check your email for the verification code.' };
    } catch (error) {
      return {
        success: false,
        message: error.message || 'Registration failed',
      };
    } finally {
      setLoading(false);
    }
  };

  const verifyEmailOTP = async (email, otp) => {
    if (!isSupabaseConfigured || !supabase) {
      return { success: false, message: 'Supabase is not configured.' };
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.verifyOtp({ email, token: otp, type: 'signup' });
      if (error) throw error;
      return { success: true };
    } catch (error) {
      return { success: false, message: error.message || 'Verification failed' };
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async (email, otp) => {
    if (!isSupabaseConfigured || !supabase) {
      return { success: false, message: 'Supabase is not configured.' };
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.verifyOtp({ email, token: otp, type: 'recovery' });
      if (error) throw error;
      return { success: true };
    } catch (error) {
      return { success: false, message: error.message || 'Verification failed' };
    } finally {
      setLoading(false);
    }
  };

  const resendEmailVerificationOTP = async (email) => {
    if (!isSupabaseConfigured || !supabase) {
      return { success: false, message: 'Supabase is not configured.' };
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.resend({ type: 'signup', email });
      if (error) throw error;
      return { success: true };
    } catch (error) {
      return { success: false, message: error.message || 'Resend failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    localStorage.removeItem('patentiq_session');
    localStorage.removeItem('patentiq_demo_session');
    if (isSupabaseConfigured && supabase) {
      try {
        await supabase.auth.signOut();
      } catch (e) {}
    }
    setUser(null);
  };

  const forgotPassword = async (email) => {
    if (!isSupabaseConfigured || !supabase) {
      return { success: false, message: 'Supabase is not configured.' };
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password',
      });
      if (error) throw error;
      return { success: true, message: 'Password reset link sent to your email.' };
    } catch (error) {
      return { success: false, message: error.message || 'Failed to send reset link' };
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (newPassword) => {
    if (!isSupabaseConfigured || !supabase) {
      return { success: false, message: 'Supabase is not configured.' };
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;
      return { success: true, message: 'Password updated successfully!' };
    } catch (error) {
      return { success: false, message: error.message || 'Failed to update password' };
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isSupabaseConfigured,
      isDemoMode: Boolean(user?.isDemo),
      login,
      loginDemo,
      googleLogin,
      register,
      logout,
      forgotPassword,
      resetPassword,
      verifyEmailOTP,
      verifyOTP,
      resendEmailVerificationOTP,
    }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

