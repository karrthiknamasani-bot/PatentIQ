import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Loader2, ShieldCheck } from 'lucide-react';
import AuthInput from '../components/AuthInput';
import GoogleLoginButton from '../components/GoogleLoginButton';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, googleLogin, loading } = useAuth();
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Simple password strength calculation
  const calculateStrength = (pass) => {
    let strength = 0;
    if (pass.length > 5) strength += 1;
    if (pass.length > 8) strength += 1;
    if (/[A-Z]/.test(pass)) strength += 1;
    if (/[0-9]/.test(pass)) strength += 1;
    if (/[^A-Za-z0-9]/.test(pass)) strength += 1;
    return strength;
  };

  const strength = calculateStrength(password);
  
  const getStrengthColor = () => {
    if (strength === 0) return 'bg-gray-200 dark:bg-gray-700';
    if (strength <= 2) return 'bg-red-500';
    if (strength <= 4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name || !email || !password || !confirmPassword) return toast.error('Please fill in all fields');
    if (password.length < 6) return toast.error('Password must be at least 6 characters');
    if (password !== confirmPassword) return toast.error('Passwords do not match');
    
    setIsSubmitting(true);
    const res = await register(name, email, password);
    setIsSubmitting(false);

    if (res.success) {
      toast.success(res.message || 'Account created successfully!');
      navigate('/verify-otp', { state: { email, type: 'verify' } });
    } else {
      toast.error(res.message);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    toast.loading('Creating account with Google...', { id: 'oauth' });
    const res = await googleLogin(credentialResponse.credential);
    if (res.success) {
      toast.success('Welcome to PatentIQ!', { id: 'oauth' });
      navigate('/dashboard');
    } else {
      toast.error(res.message, { id: 'oauth' });
    }
  };

  const handleGoogleError = () => {
    toast.error('Google Sign-Up failed');
  };

  const isButtonDisabled = loading || isSubmitting || !name || !email || !password || !confirmPassword || password !== confirmPassword;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#f8fafc] dark:bg-[#050b14] relative font-sans transition-colors duration-300 overflow-hidden py-12">
      {/* Premium Background Glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1000px] h-[500px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-600/20 via-blue-900/5 to-transparent dark:from-purple-600/10 dark:via-transparent pointer-events-none blur-[100px]" />

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
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Create an account</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Join PatentIQ to start analyzing patents.</p>
        </div>

        <form onSubmit={handleRegister}>
          <AuthInput 
            icon={User}
            type="text"
            name="name"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
          />
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
          <div className="mb-2">
            <AuthInput 
              icon={Lock}
              type="password"
              name="password"
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="mb-6 px-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character (e.g., @, $, !, %, *, ?, &).
          </div>
          
          {/* Password Strength Indicator */}
          {password && (
            <div className="flex gap-1 mb-4 mt-[-8px] px-1">
              {[...Array(5)].map((_, i) => (
                <div 
                  key={i} 
                  className={`h-1 flex-1 rounded-full transition-colors duration-300 ${i < strength ? getStrengthColor() : 'bg-gray-200 dark:bg-gray-800'}`}
                />
              ))}
            </div>
          )}

          <AuthInput 
            icon={ShieldCheck}
            type="password"
            name="confirmPassword"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            error={confirmPassword && password !== confirmPassword ? 'Passwords do not match' : null}
          />

          <motion.button 
            disabled={isButtonDisabled} 
            whileHover={{ scale: isButtonDisabled ? 1 : 1.01 }}
            whileTap={{ scale: isButtonDisabled ? 1 : 0.98 }}
            type="submit" 
            className="relative mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl text-sm transition-all overflow-hidden disabled:opacity-70 disabled:cursor-not-allowed group"
          >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-blue-600 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            <span className="relative flex items-center justify-center gap-2">
              {(loading || isSubmitting) ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating account...
                </>
              ) : 'Sign Up'}
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
          Already have an account? <Link to="/login" className="text-blue-600 hover:text-blue-700 dark:text-blue-500 dark:hover:text-blue-400 font-medium ml-1 transition-colors">Sign in</Link>
        </div>
      </motion.div>
    </div>
  );
};

export default RegisterPage;
