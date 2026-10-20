import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Mail, Lock, Loader2 } from 'lucide-react';
import AuthInput from '../components/AuthInput';
import GoogleLoginButton from '../components/GoogleLoginButton';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, loginDemo, googleLogin, loading, isSupabaseConfigured } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const savedEmail = localStorage.getItem('rememberedEmail');
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  const handleDemoLogin = () => {
    loginDemo();
    toast.success('Welcome! Active in Demo Mode');
    navigate('/dashboard');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) return toast.error('Please fill in all fields');
    
    setIsSubmitting(true);
    if (rememberMe) {
      localStorage.setItem('rememberedEmail', email);
    } else {
      localStorage.removeItem('rememberedEmail');
    }

    const res = await login(email, password);
    setIsSubmitting(false);

    if (res.success) {
      toast.success('Welcome back!');
      navigate('/dashboard');
    } else {
      toast.error(res.message);
      if (res.unverified) {
        navigate('/verify-otp', { state: { email, type: 'verify' } });
      }
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    toast.loading('Verifying Google token...', { id: 'oauth' });
    const res = await googleLogin(credentialResponse.credential);
    if (res.success) {
      toast.success('Logged in with Google', { id: 'oauth' });
      navigate('/dashboard');
    } else {
      toast.error(res.message, { id: 'oauth' });
    }
  };

  const handleGoogleError = () => {
    toast.error('Google Sign-In failed');
  };

  const isButtonDisabled = loading || isSubmitting || !email || !password;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#f8fafc] dark:bg-[#050b14] relative font-sans transition-colors duration-300 overflow-hidden">
      {/* Premium Background Glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1000px] h-[500px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-600/20 via-blue-900/5 to-transparent dark:from-blue-600/10 dark:via-transparent pointer-events-none blur-[100px]" />
      
      {/* Logo Section */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center mb-8 z-10"
      >
        <Link to="/" className="flex items-center hover:opacity-80 transition-opacity">
          <span className="text-4xl font-black tracking-tighter text-gray-900 dark:text-white drop-shadow-sm">
            Patent<span className="text-blue-600 dark:text-blue-500">IQ</span>
          </span>
        </Link>
      </motion.div>

      {/* Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-[420px] bg-white/70 dark:bg-[#0a0f1c]/70 backdrop-blur-2xl border border-white/50 dark:border-white/10 rounded-3xl p-8 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.1)] dark:shadow-[0_8px_40px_-12px_rgba(0,0,0,0.5)] z-10 relative"
      >
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Welcome back</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Enter your credentials to access your account.</p>
        </div>

        {!isSupabaseConfigured && (
          <div className="mb-6 p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs">
            <div className="font-semibold mb-1 flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              Demo Mode — Supabase is not configured.
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-2.5">
              Remote Supabase credentials are not detected. You can enter with the deterministic local demo identity to test the full pipeline.
            </p>
            <button
              type="button"
              onClick={handleDemoLogin}
              className="w-full py-2 px-3 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-xl text-xs transition-colors shadow-sm"
            >
              Continue in Demo Mode (Local Evaluator)
            </button>
          </div>
        )}

        <form onSubmit={handleLogin}>
          <AuthInput 
            icon={Mail}
            type="email"
            name="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <AuthInput 
            icon={Lock}
            type="password"
            name="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <div className="flex items-center justify-between mb-6 mt-2">
            <label className="flex items-center gap-2 cursor-pointer group">
              <div className="relative flex items-center justify-center">
                <input 
                  type="checkbox" 
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="peer appearance-none w-4 h-4 rounded-md border border-gray-300 dark:border-gray-600 checked:bg-blue-600 checked:border-blue-600 bg-transparent transition-all cursor-pointer" 
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 5L4.5 8.5L13 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-colors select-none">Remember me</span>
            </label>
            <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-500 dark:hover:text-blue-400 transition-colors font-medium">
              Forgot password?
            </Link>
          </div>

          <motion.button 
            disabled={isButtonDisabled} 
            whileHover={{ scale: isButtonDisabled ? 1 : 1.01 }}
            whileTap={{ scale: isButtonDisabled ? 1 : 0.98 }}
            type="submit" 
            className="relative w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl text-sm transition-all overflow-hidden disabled:opacity-70 disabled:cursor-not-allowed group"
          >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-blue-600 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            <span className="relative flex items-center justify-center gap-2">
              {(loading || isSubmitting) ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Authenticating...
                </>
              ) : 'Sign In'}
            </span>
          </motion.button>
        </form>

        <div className="flex items-center my-6">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-800 to-transparent"></div>
          <span className="px-3 text-[11px] font-medium text-gray-400 dark:text-gray-500 tracking-wider">OR</span>
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-800 to-transparent"></div>
        </div>

        <GoogleLoginButton 
          onSuccess={handleGoogleSuccess} 
          onError={handleGoogleError} 
        />

        <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          New to PatentIQ? <Link to="/register" className="text-blue-600 hover:text-blue-700 dark:text-blue-500 dark:hover:text-blue-400 font-medium ml-1 transition-colors">Create an account</Link>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
