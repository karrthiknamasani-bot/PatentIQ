import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Mail, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AuthInput from '../components/AuthInput';
import toast from 'react-hot-toast';

const ForgotPasswordPage = () => {
  const { forgotPassword, loading } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return toast.error('Please enter your email address');

    setIsSubmitting(true);
    const res = await forgotPassword(email);
    setIsSubmitting(false);

    if (res.success) {
      toast.success('OTP sent successfully!');
      navigate('/verify-otp', { state: { email } });
    } else {
      toast.error(res.message);
    }
  };

  const isButtonDisabled = loading || isSubmitting || !email;

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
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Reset password</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Enter your email and we'll send you an OTP to reset your password.</p>
        </div>

        <form onSubmit={handleSubmit}>
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

          <motion.button 
            disabled={isButtonDisabled} 
            whileHover={{ scale: isButtonDisabled ? 1 : 1.01 }}
            whileTap={{ scale: isButtonDisabled ? 1 : 0.98 }}
            type="submit" 
            className="relative mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl text-sm transition-all overflow-hidden disabled:opacity-70 disabled:cursor-not-allowed group"
          >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-blue-600 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            <span className="relative flex items-center justify-center gap-2">
              {(loading || isSubmitting) ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : 'Send OTP'}
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

export default ForgotPasswordPage;
