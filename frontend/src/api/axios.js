import axios from 'axios';
import { supabase, isSupabaseConfigured } from './supabase';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 60000, // 60 seconds for full AI patent pipeline executions
});

api.interceptors.request.use(async (config) => {
  // If Supabase is configured and has an active session, attach its access token
  if (isSupabaseConfigured && supabase) {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session && session.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
        return config;
      }
    } catch (e) {
      console.warn('Unable to get Supabase session token:', e);
    }
  }

  // Check for authenticated Google or local session token
  const authSession = localStorage.getItem('patentiq_session');
  if (authSession) {
    try {
      const parsed = JSON.parse(authSession);
      if (parsed.token) {
        config.headers.Authorization = `Bearer ${parsed.token}`;
        return config;
      }
    } catch (e) {}
  }

  // Fallback: Check for demo session token
  const demoSession = localStorage.getItem('patentiq_demo_session');
  if (demoSession) {
    try {
      const parsed = JSON.parse(demoSession);
      if (parsed.token) {
        config.headers.Authorization = `Bearer ${parsed.token}`;
        return config;
      }
    } catch (e) {}
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export default api;

