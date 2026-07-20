import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';

const AuthInput = ({ 
  icon: Icon, 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  required = false,
  autoComplete,
  name,
  error
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;

  return (
    <div className="relative mb-4 w-full">
      <motion.div
        animate={{
          borderColor: error ? '#ef4444' : isFocused ? '#3b82f6' : 'rgba(55, 65, 81, 0.4)',
          boxShadow: error ? '0 0 0 1px rgba(239, 68, 68, 0.2)' : isFocused ? '0 0 0 2px rgba(59, 130, 246, 0.2)' : '0 0 0 0px rgba(0,0,0,0)'
        }}
        transition={{ duration: 0.2 }}
        className="relative flex items-center w-full bg-white/5 dark:bg-[#0a0f1c]/50 backdrop-blur-md border rounded-xl overflow-hidden transition-colors"
      >
        <div className="pl-4 flex items-center justify-center text-gray-500 dark:text-gray-400">
          <Icon size={18} className={isFocused ? 'text-blue-500' : ''} style={{ transition: 'color 0.2s' }} />
        </div>
        
        <input
          name={name}
          type={inputType}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          required={required}
          autoComplete={autoComplete}
          className="w-full bg-transparent border-none px-3 py-3.5 text-[15px] font-medium text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:ring-0"
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="pr-4 flex items-center justify-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus:outline-none transition-colors"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </motion.div>
      
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="text-xs text-red-500 mt-1.5 ml-1 absolute"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AuthInput;
