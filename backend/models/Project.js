const mongoose = require('mongoose');

const projectSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'User',
  },
  title: {
    type: String,
    required: [true, 'Please provide a project title'],
  },
  description: {
    type: String,
  },
  originalFileName: {
    type: String,
    required: true,
  },
  storedFileName: {
    type: String,
    required: true,
  },
  filePath: {
    type: String,
    required: true,
  },
  fileType: {
    type: String,
    required: true,
  },
  fileSize: {
    type: Number,
    required: true,
  },
  uploadDate: {
    type: Date,
    default: Date.now,
  },
  status: {
    type: String,
    enum: ['uploaded', 'processing', 'processed', 'analyzing', 'completed', 'failed'],
    default: 'uploaded',
  },
  processingStage: {
    type: String,
  },
  extractedText: {
    type: String,
  },
  extractedMetadata: {
    type: mongoose.Schema.Types.Mixed,
  },
  errorMessage: {
    type: String,
  },
  processingStartedAt: {
    type: Date,
  },
  processingCompletedAt: {
    type: Date,
  },
  processingDuration: {
    type: Number,
  },
  patentPotentialScore: {
    type: Number,
    default: null,
  },
  noveltyScore: {
    type: Number,
    default: null,
  },
  similarityScore: {
    type: Number,
    default: null,
  },
  aiSummary: {
    type: String,
    default: null,
  },
  reportGenerated: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Number,
    default: 0,
  },
  processingError: {
    type: String,
  },
  technicalDomain: { type: String },
  innovationSummary: { type: String },
  strengths: { type: [String], default: [] },
  weaknesses: { type: [String], default: [] },
  commercialApplications: { type: [String], default: [] },
  recommendation: { type: String },
  confidence: { type: Number },
  analysisModel: { type: String },
  analysisTimestamp: { type: Date }
}, { timestamps: true });

module.exports = mongoose.model('Project', projectSchema);
