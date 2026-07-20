const mongoose = require('mongoose');

const analysisSchema = new mongoose.Schema({
  projectId: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'Project',
  },
  analysis: {
    type: mongoose.Schema.Types.Mixed,
    required: true, // The raw parsed JSON response from Gemini
  },
  scores: {
    noveltyScore: { type: Number, default: 0 },
    similarityScore: { type: Number, default: 0 },
    innovationScore: { type: Number, default: 0 },
    confidenceScore: { type: Number, default: 0 },
  },
  retrievedPatents: {
    type: [String], // Array of patent IDs or PatentNumbers that were referenced
    default: [],
  },
  modelUsed: {
    type: String,
    required: true,
    default: 'gemini-embedding-2 + gemini-3.1-flash-lite',
  },
  processingTime: {
    type: Number,
    required: true,
  },
  retrievedChunkCount: {
    type: Number,
    default: 0,
  },
  analysisVersion: {
    type: String,
    default: '1.0'
  },
  status: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    default: 'completed',
  }
}, { timestamps: true });

module.exports = mongoose.model('Analysis', analysisSchema);
