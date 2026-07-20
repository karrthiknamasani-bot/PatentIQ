const User = require('../models/User');
const generateToken = require('../utils/generateToken');
const { OAuth2Client } = require('google-auth-library');

const client = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

// @desc    Register a new user
// @route   POST /api/auth/register
// @access  Public
const registerUser = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ success: false, message: 'Please provide all fields' });
    }

    const userExists = await User.findOne({ email });
    if (userExists) {
      return res.status(400).json({ success: false, message: 'User already exists' });
    }

    const user = await User.create({
      name,
      email,
      password,
      isVerified: false
    });

    if (user) {
      const otp = user.generateOTP('verify');
      await user.save({ validateBeforeSave: false });

      // Print to console ONLY in development
      if (process.env.NODE_ENV === 'development') {
        console.log('\n--------------------------------');
        console.log('Email Verification OTP');
        console.log('Email:', user.email);
        console.log('OTP:', otp);
        console.log('Expires in 5 minutes');
        console.log('--------------------------------\n');
      }

      try {
        const sendEmail = require('../utils/sendEmail');
        await sendEmail({
          email: user.email,
          type: 'verify',
          otp
        });
      } catch (err) {
        console.error('Email verification send failed:', err);
      }

      res.status(201).json({
        success: true,
        message: 'Registration successful. Please verify your email.',
        unverified: true,
        email: user.email
      });
    } else {
      res.status(400).json({ success: false, message: 'Invalid user data' });
    }
  } catch (error) {
    if (error.name === 'ValidationError') {
      const messages = Object.values(error.errors).map(val => val.message);
      return res.status(400).json({ success: false, message: messages.join(', ') });
    }
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Auth user & get token
// @route   POST /api/auth/login
// @access  Public
const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ success: false, message: 'Please provide email and password' });
    }

    const user = await User.findOne({ email }).select('+password');

    if (!user) {
      return res.status(401).json({ success: false, message: 'Invalid email or password' });
    }

    // Check login lockout
    if (user.loginLockUntil && user.loginLockUntil > Date.now()) {
      return res.status(403).json({ success: false, message: 'Account is temporarily locked. Please try again after 15 minutes.' });
    }

    if (await user.matchPassword(password)) {
      // Reset login attempts on success
      user.loginAttempts = 0;
      user.loginLockUntil = undefined;
      await user.save({ validateBeforeSave: false });

      // Check if user is explicitly unverified
      if (user.isVerified === false) {
        return res.status(403).json({ 
          success: false, 
          message: 'Please verify your email before logging in.',
          unverified: true,
          email: user.email
        });
      }

      res.json({
        success: true,
        message: 'Logged in successfully',
        data: {
          _id: user._id,
          name: user.name,
          email: user.email,
          token: generateToken(user._id),
        }
      });
    } else {
      user.loginAttempts += 1;
      if (user.loginAttempts >= 5) {
        user.loginLockUntil = Date.now() + 15 * 60 * 1000; // 15 mins lock
      }
      await user.save({ validateBeforeSave: false });

      res.status(401).json({ success: false, message: 'Invalid email or password' });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get user profile
// @route   GET /api/auth/me
// @access  Private
const getUserProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user._id);

    if (user) {
      res.json({
        success: true,
        message: 'User profile retrieved successfully',
        data: {
          _id: user._id,
          name: user.name,
          email: user.email,
        }
      });
    } else {
      res.status(404).json({ success: false, message: 'User not found' });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Real Google OAuth Login / Register
// @route   POST /api/auth/google
// @access  Public
const googleAuth = async (req, res) => {
  try {
    const { idToken } = req.body;
    
    if (!idToken) {
      return res.status(400).json({ success: false, message: 'Google ID Token is missing' });
    }

    // Verify token with Google
    const ticket = await client.verifyIdToken({
      idToken,
      audience: process.env.GOOGLE_CLIENT_ID,
    });
    
    const payload = ticket.getPayload();
    const { sub: googleId, email, name, picture: avatar } = payload;

    let user = await User.findOne({ email });
    
    if (!user) {
      // Auto-create account
      user = await User.create({
        name,
        email,
        provider: 'google',
        googleId,
        avatar,
        isVerified: true
      });
    } else {
      // Existing user: Link google ID if not linked, update avatar if missing
      let isModified = false;
      if (user.provider === 'local') {
        user.provider = 'google';
        isModified = true;
      }
      if (!user.googleId) {
        user.googleId = googleId;
        isModified = true;
      }
      if (!user.avatar && avatar) {
        user.avatar = avatar;
        isModified = true;
      }
      if (user.isVerified === false) {
        user.isVerified = true;
        isModified = true;
      }
      if (isModified) await user.save();
    }

    res.json({
      success: true,
      message: 'Logged in successfully with Google',
      data: {
        _id: user._id,
        name: user.name,
        email: user.email,
        avatar: user.avatar,
        token: generateToken(user._id),
      }
    });

  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Forgot password (Generate OTP)
// @route   POST /api/auth/forgot-password
// @access  Public
const forgotPassword = async (req, res) => {
  try {
    const user = await User.findOne({ email: req.body.email });

    if (!user) {
      return res.status(404).json({ success: false, message: 'There is no user with that email' });
    }

    // Get reset OTP
    const otp = user.generateOTP('reset');
    await user.save({ validateBeforeSave: false });

    // Print to console ONLY in development
    if (process.env.NODE_ENV === 'development') {
      console.log('\n--------------------------------');
      console.log('Password Reset OTP');
      console.log('Email:');
      console.log(user.email);
      console.log('OTP:');
      console.log(otp);
      console.log('Expires in 5 minutes');
      console.log('--------------------------------\n');
    }

    try {
      const sendEmail = require('../utils/sendEmail');
      await sendEmail({
        email: user.email,
        subject: 'PatentIQ Password Reset OTP',
        otp
      });

      res.status(200).json({ success: true, message: 'OTP generated and sent successfully' });
    } catch (err) {
      console.error(err);
      user.resetOTP = undefined;
      user.resetOTPExpire = undefined;
      await user.save({ validateBeforeSave: false });

      return res.status(500).json({ success: false, message: 'Email could not be sent' });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Verify OTP
// @route   POST /api/auth/verify-otp
// @access  Public
const verifyOTP = async (req, res) => {
  try {
    const { email, otp } = req.body;
    
    if (!email || !otp) {
      return res.status(400).json({ success: false, message: 'Please provide email and OTP' });
    }

    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ success: false, message: 'User not found' });
    }

    if (user.otpLockUntil && user.otpLockUntil > Date.now()) {
      return res.status(403).json({ success: false, message: 'Too many failed OTP attempts. Please try again after 15 minutes.' });
    }

    const crypto = require('crypto');
    const hashedOTP = crypto
      .createHash('sha256')
      .update(otp)
      .digest('hex');

    if (user.resetOTP !== hashedOTP || user.resetOTPExpire < Date.now()) {
      user.otpAttempts += 1;
      if (user.otpAttempts >= 5) {
        user.otpLockUntil = Date.now() + 15 * 60 * 1000;
      }
      await user.save({ validateBeforeSave: false });
      return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
    }

    user.otpAttempts = 0;
    user.otpLockUntil = undefined;
    await user.save({ validateBeforeSave: false });

    res.status(200).json({ success: true, message: 'OTP verified successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Reset password
// @route   POST /api/auth/reset-password
// @access  Public
const resetPassword = async (req, res) => {
  try {
    const { email, otp, newPassword } = req.body;
    
    if (!email || !otp || !newPassword) {
      return res.status(400).json({ success: false, message: 'Please provide email, OTP, and new password' });
    }

    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ success: false, message: 'User not found' });
    }

    if (user.otpLockUntil && user.otpLockUntil > Date.now()) {
      return res.status(403).json({ success: false, message: 'Too many failed OTP attempts. Please try again after 15 minutes.' });
    }

    const crypto = require('crypto');
    const hashedOTP = crypto
      .createHash('sha256')
      .update(otp)
      .digest('hex');

    if (user.resetOTP !== hashedOTP || user.resetOTPExpire < Date.now()) {
      user.otpAttempts += 1;
      if (user.otpAttempts >= 5) {
        user.otpLockUntil = Date.now() + 15 * 60 * 1000;
      }
      await user.save({ validateBeforeSave: false });
      return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
    }

    // Set new password, reset lockouts
    user.password = newPassword;
    user.resetOTP = undefined;
    user.resetOTPExpire = undefined;
    user.otpAttempts = 0;
    user.otpLockUntil = undefined;
    user.loginAttempts = 0;
    user.loginLockUntil = undefined;
    
    await user.save();

    res.json({
      success: true,
      message: 'Password reset successfully',
      data: {
        _id: user._id,
        name: user.name,
        email: user.email,
        avatar: user.avatar,
        token: generateToken(user._id),
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Verify email OTP
// @route   POST /api/auth/verify-email-otp
// @access  Public
const verifyEmailOTP = async (req, res) => {
  try {
    const { email, otp } = req.body;
    
    if (!email || !otp) {
      return res.status(400).json({ success: false, message: 'Please provide email and OTP' });
    }

    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ success: false, message: 'User not found' });
    }

    if (user.otpLockUntil && user.otpLockUntil > Date.now()) {
      return res.status(403).json({ success: false, message: 'Too many failed OTP attempts. Please try again after 15 minutes.' });
    }

    const crypto = require('crypto');
    const hashedOTP = crypto
      .createHash('sha256')
      .update(otp)
      .digest('hex');

    if (user.emailVerificationOTP !== hashedOTP || user.emailVerificationOTPExpire < Date.now()) {
      user.otpAttempts += 1;
      if (user.otpAttempts >= 5) {
        user.otpLockUntil = Date.now() + 15 * 60 * 1000;
      }
      await user.save({ validateBeforeSave: false });
      return res.status(400).json({ success: false, message: 'Invalid or expired OTP' });
    }

    user.isVerified = true;
    user.emailVerificationOTP = undefined;
    user.emailVerificationOTPExpire = undefined;
    user.otpAttempts = 0;
    user.otpLockUntil = undefined;
    await user.save({ validateBeforeSave: false });

    res.status(200).json({ success: true, message: 'Email verified successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Resend verification email OTP
// @route   POST /api/auth/resend-verification-otp
// @access  Public
const resendEmailVerificationOTP = async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) return res.status(400).json({ success: false, message: 'Please provide an email' });

    const user = await User.findOne({ email });

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    if (user.isVerified) {
      return res.status(400).json({ success: false, message: 'Email is already verified' });
    }

    const otp = user.generateOTP('verify');
    await user.save({ validateBeforeSave: false });

    if (process.env.NODE_ENV === 'development') {
      console.log('\n--------------------------------');
      console.log('Resend Email Verification OTP');
      console.log('Email:', user.email);
      console.log('OTP:', otp);
      console.log('Expires in 5 minutes');
      console.log('--------------------------------\n');
    }

    const sendEmail = require('../utils/sendEmail');
    await sendEmail({
      email: user.email,
      type: 'verify',
      otp
    });

    res.status(200).json({ success: true, message: 'Verification OTP resent successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = {
  registerUser,
  loginUser,
  getUserProfile,
  googleAuth,
  forgotPassword,
  verifyOTP,
  resetPassword,
  verifyEmailOTP,
  resendEmailVerificationOTP
};
