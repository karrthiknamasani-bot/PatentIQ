const mongoose = require('mongoose');

const patentSchema = new mongoose.Schema({
  patentNumber: {
    type: String,
    required: true,
    unique: true,
    trim: true,
  },
  title: {
    type: String,
    required: true,
  },
  abstract: {
    type: String,
    required: true,
  },
  inventors: {
    type: [String],
    default: [],
  },
  assignee: {
    type: String,
  },
  publicationDate: {
    type: Date,
  },
  ipcClasses: {
    type: [String],
    default: [],
  },
  source: {
    type: String,
    enum: ['uspto', 'epo', 'wipo', 'google_patents', 'custom'],
    default: 'custom',
  },
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {},
  }
}, { timestamps: true });

module.exports = mongoose.model('Patent', patentSchema);
