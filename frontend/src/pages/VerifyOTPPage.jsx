import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, KeyRound, Loader2, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AuthInput from '../components/AuthInput';
import toast from 'react-hot-toast';

const VerifyOTPPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyOTP, forgotPassword, verifyEmailOTP, resendEmailVerificationOTP, loading } = useAuth();
  
  const email = location.state?.email;
  const type = location.state?.type || 'reset';
  
  const [otp, setOtp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes

  useEffect(() => {
    if (timeLeft <= 0) return;

    const timerId = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timerId);
  }, [timeLeft]);

  // Redirect if accessed directly without email
  if (!email) {
    return <Navigate to="/forgot-password" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!otp || otp.length < 6) return toast.error('Please enter a valid 6-digit OTP');

    setIsSubmitting(true);
    let res;
    if (type === 'verify') {
      res = await verifyEmailOTP(email, otp);
    } else {
      res = await verifyOTP(email, otp);
    }
    setIsSubmitting(false);

    if (res.success) {
      if (type === 'verify') {
        toast.success('Email verified successfully! You can now log in.');
        navigate('/login');
      } else {
        toast.success('OTP verified successfully!');
        navigate('/reset-password', { state: { email, otp } });
      }
    } else {
      toast.error(res.message);
    }
  };

  const handleResend = async () => {
    let res;
    if (type === 'verify') {
      res = await resendEmailVerificationOTP(email);
    } else {
      res = await forgotPassword(email);
    }
    
    if (res.success) {
      toast.success('New OTP sent successfully!');
      setTimeLeft(300);
      setOtp('');
    } else {
      toast.error(res.message);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const isButtonDisabled = loading || isSubmitting || !otp || otp.length < 6;

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
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <KeyRound className="text-blue-600 dark:text-blue-400" size={32} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {type === 'verify' ? 'Verify Email' : 'Verify OTP'}
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Enter the 6-digit verification code sent to <br/><span className="font-medium text-gray-900 dark:text-gray-200">{email}</span></p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <AuthInput 
              icon={KeyRound}
              type="text"
              name="otp"
              placeholder="6-digit OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, '').slice(0, 6))}
              required
              autoComplete="one-time-code"
            />
          </div>

          <div className="flex justify-between items-center mb-6 px-1">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Expires in: <span className="font-mono font-medium text-gray-900 dark:text-gray-200">{formatTime(timeLeft)}</span>
            </span>
            <button
              type="button"
              onClick={handleResend}
              disabled={timeLeft > 0 || loading}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-500 dark:hover:text-blue-400 disabled:text-gray-400 dark:disabled:text-gray-600 transition-colors flex items-center gap-1"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Resend OTP
            </button>
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
                  Verifying...
                </>
              ) : (type === 'verify' ? 'Verify Email' : 'Verify OTP')}
            </span>
          </motion.button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors">
            <ArrowLeft size={16} className="mr-2" />
            Back to login
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default VerifyOTPPage;
