const mongoose = require('mongoose');

const reportSchema = new mongoose.Schema({
  projectId: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'Project',
  },
  analysisId: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'Analysis',
  },
  reportType: {
    type: String,
    enum: ['pdf', 'json', 'markdown'],
    required: true,
  },
  reportPath: {
    type: String,
    required: true,
  },
  generatedBy: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'User',
  },
  status: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    default: 'pending',
  }
}, { timestamps: true });

module.exports = mongoose.model('Report', reportSchema);
