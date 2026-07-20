import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { motion } from 'framer-motion';

const GoogleLoginButton = ({ onSuccess, onError }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      className="w-full flex items-center justify-center overflow-hidden rounded-xl transition-all hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]"
    >
      <GoogleLogin
        onSuccess={onSuccess}
        onError={onError}
        theme="filled_black"
        size="large"
        shape="pill"
        width="100%"
        text="continue_with"
      />
    </motion.div>
  );
};

export default GoogleLoginButton;
