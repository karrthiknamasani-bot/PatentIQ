import React, { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, Loader2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AuthInput from '../components/AuthInput';
import toast from 'react-hot-toast';

const ResetPasswordPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { resetPassword, loading } = useAuth();
  
  const email = location.state?.email;
  const otp = location.state?.otp;
  
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

  // Redirect if accessed directly without email/otp
  if (!email || !otp) {
    return <Navigate to="/forgot-password" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password || !confirmPassword) return toast.error('Please fill in all fields');
    if (password.length < 6) return toast.error('Password must be at least 6 characters');
    if (password !== confirmPassword) return toast.error('Passwords do not match');

    setIsSubmitting(true);
    const res = await resetPassword(email, otp, password);
    setIsSubmitting(false);

    if (res.success) {
      toast.success('Password reset successfully!');
      navigate('/dashboard');
    } else {
      toast.error(res.message);
    }
  };

  const isButtonDisabled = loading || isSubmitting || !password || !confirmPassword || password !== confirmPassword;

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
        <div className="flex items-center">
          <span className="text-4xl font-black tracking-tighter text-gray-900 dark:text-white drop-shadow-sm">
            Patent<span className="text-blue-600 dark:text-blue-500">IQ</span>
          </span>
        </div>
      </motion.div>

      {/* Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-[420px] bg-white/70 dark:bg-[#0a0f1c]/70 backdrop-blur-2xl border border-white/50 dark:border-white/10 rounded-3xl p-8 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.1)] dark:shadow-[0_8px_40px_-12px_rgba(0,0,0,0.5)] z-10 relative"
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Create new password</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Your new password must be different from previous used passwords.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <AuthInput 
            icon={Lock}
            type="password"
            name="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
          />

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
            placeholder="Confirm new password"
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
                  Resetting...
                </>
              ) : 'Reset Password'}
            </span>
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
};

export default ResetPasswordPage;
