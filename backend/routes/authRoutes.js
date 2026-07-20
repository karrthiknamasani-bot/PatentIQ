const express = require('express');
const router = express.Router();
const rateLimit = require('express-rate-limit');
const { registerUser, loginUser, getUserProfile, googleAuth, forgotPassword, verifyOTP, resetPassword, verifyEmailOTP, resendEmailVerificationOTP } = require('../controllers/authController');
const { protect } = require('../middleware/authMiddleware');

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many login attempts, please try again after 15 minutes' }
});

const registerLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many accounts created from this IP, please try again after an hour' }
});

const forgotPasswordLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 3,
  message: { success: false, message: 'Too many password reset requests, please try again after 15 minutes' }
});

const otpLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { success: false, message: 'Too many OTP verification attempts, please try again after 15 minutes' }
});

router.post('/register', registerLimiter, registerUser);
router.post('/login', loginLimiter, loginUser);
router.post('/google', googleAuth);
router.post('/forgot-password', forgotPasswordLimiter, forgotPassword);
router.post('/verify-otp', otpLimiter, verifyOTP);
router.post('/reset-password', resetPassword);
router.get('/me', protect, getUserProfile);
router.post('/verify-email-otp', otpLimiter, verifyEmailOTP);
router.post('/resend-verification-otp', forgotPasswordLimiter, resendEmailVerificationOTP);

module.exports = router;
