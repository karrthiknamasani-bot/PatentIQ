require('dotenv').config();
console.log("Gemini Key:", process.env.GEMINI_API_KEY);
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const mongoSanitize = require('express-mongo-sanitize');
const morgan = require('morgan');
const connectDB = require('./config/db');
const { errorHandler, notFound } = require('./middleware/errorMiddleware');

// Import routes
const healthRoutes = require('./routes/healthRoutes');
const authRoutes = require('./routes/authRoutes');
const projectRoutes = require('./routes/projectRoutes');
const processRoutes = require('./routes/processRoutes');
const patentRoutes = require('./routes/patentRoutes');
const searchRoutes = require('./routes/searchRoutes');
const analysisRoutes = require('./routes/analysisRoutes');
const reportRoutes = require('./routes/reportRoutes');

// Initialize app
const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors());
app.use(helmet());

// Express 5 makes req.query a getter, so express-mongo-sanitize crashes if used globally.
// We manually sanitize body and params instead.
app.use((req, res, next) => {
  if (req.body) req.body = mongoSanitize.sanitize(req.body);
  if (req.params) req.params = mongoSanitize.sanitize(req.params);
  if (req.headers) req.headers = mongoSanitize.sanitize(req.headers);
  next();
});

if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'));
}

// Routes
app.use('/api/health', healthRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/projects', projectRoutes);
app.use('/api/process', processRoutes);
app.use('/api/patents', patentRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/analyze', analysisRoutes);
app.use('/api/report', reportRoutes);

// Connect to Database
connectDB();

// Handle unmatched routes
app.use(notFound);

// Global Error Handler
app.use(errorHandler);

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running in ${process.env.NODE_ENV} mode on port ${PORT}`);
});
