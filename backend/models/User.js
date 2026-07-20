const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Please add a name'],
  },
  email: {
    type: String,
    required: [true, 'Please add an email'],
    unique: true,
    match: [
      /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/,
      'Please add a valid email',
    ],
  },
  password: {
    type: String,
    minlength: [8, 'Password must be at least 8 characters'],
    validate: {
      validator: function (v) {
        // Must contain uppercase, lowercase, number, and special character
        return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(v);
      },
      message: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
    },
    select: false,
    // Not required because OAuth users might not have a password
  },
  provider: {
    type: String,
    enum: ['local', 'google'],
    default: 'local'
  },
  googleId: {
    type: String,
    default: null
  },
  avatar: {
    type: String,
    default: null
  },
  loginAttempts: {
    type: Number,
    default: 0
  },
  loginLockUntil: {
    type: Date
  },
  otpAttempts: {
    type: Number,
    default: 0
  },
  otpLockUntil: {
    type: Date
  },
  resetOTP: String,
  resetOTPExpire: Date,
  isVerified: {
    type: Boolean,
    default: false
  },
  emailVerificationOTP: String,
  emailVerificationOTPExpire: Date
}, { timestamps: true });

// Encrypt password before saving (if it exists)
userSchema.pre('save', async function () {
  if (!this.isModified('password') || !this.password) {
    return;
  }
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
});

// Match user entered password to hashed password in database
userSchema.methods.matchPassword = async function (enteredPassword) {
  return await bcrypt.compare(enteredPassword, this.password);
};

// Generate and hash OTP for both Verification and Reset
userSchema.methods.generateOTP = function (type) {
  // type should be 'reset' or 'verify'
  
  // Reset lock and attempts for new OTPs
  this.otpAttempts = 0;
  this.otpLockUntil = undefined;

  // Generate a 6 digit random number
  const otp = Math.floor(100000 + Math.random() * 900000).toString();

  // Hash OTP
  const crypto = require('crypto');
  const hashedOTP = crypto
    .createHash('sha256')
    .update(otp)
    .digest('hex');

  // Set expire (5 minutes)
  const expireDate = Date.now() + 5 * 60 * 1000;

  if (type === 'reset') {
    this.resetOTP = hashedOTP;
    this.resetOTPExpire = expireDate;
  } else if (type === 'verify') {
    this.emailVerificationOTP = hashedOTP;
    this.emailVerificationOTPExpire = expireDate;
  }

  return otp;
};

module.exports = mongoose.model('User', userSchema);
