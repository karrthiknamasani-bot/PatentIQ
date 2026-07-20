const mongoose = require('mongoose');

const documentChunkSchema = new mongoose.Schema({
  projectId: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'Project',
  },
  chunkIndex: {
    type: Number,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  startCharacter: {
    type: Number,
    required: true,
  },
  endCharacter: {
    type: Number,
    required: true,
  },
  tokenEstimate: {
    type: Number,
    required: true,
  },
  embeddingStatus: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    default: 'pending',
  }
}, { timestamps: true });

// Compound index for querying chunks of a specific project in order
documentChunkSchema.index({ projectId: 1, chunkIndex: 1 });

module.exports = mongoose.model('DocumentChunk', documentChunkSchema);
