const mongoose = require('mongoose');

const patentChunkSchema = new mongoose.Schema({
  patentId: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'Patent',
  },
  chunkIndex: {
    type: Number,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {},
  },
  embeddingStatus: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    default: 'pending',
  }
}, { timestamps: { createdAt: true, updatedAt: false } });

// Compound index for querying chunks of a specific patent in order
patentChunkSchema.index({ patentId: 1, chunkIndex: 1 });

module.exports = mongoose.model('PatentChunk', patentChunkSchema);
