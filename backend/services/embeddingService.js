const GeminiEmbeddingProvider = require('./providers/GeminiEmbeddingProvider');
const chromaService = require('./chromaService');
const DocumentChunk = require('../models/DocumentChunk');
const PatentChunk = require('../models/PatentChunk');

class EmbeddingService {
  constructor() {
    this.batchSize = 20; // safe batch size for Gemini rate limits
  }

  get provider() {
    if (!this._provider) {
      this._provider = new GeminiEmbeddingProvider(process.env.GEMINI_API_KEY);
    }
    return this._provider;
  }

  /**
   * Embed and store user document chunks
   * @param {string} projectId 
   */
  async processProjectEmbeddings(projectId) {
    try {
      const chunks = await DocumentChunk.find({ 
        projectId, 
        embeddingStatus: { $ne: 'completed' } 
      }).sort({ chunkIndex: 1 });

      if (chunks.length === 0) return;

      await this._processBatches(chunks, 'document');
    } catch (error) {
      console.error(`Failed to process document embeddings for project ${projectId}:`, error);
    }
  }

  /**
   * Embed and store patent chunks
   * @param {string} patentId 
   */
  async processPatentEmbeddings(patentId) {
    try {
      const chunks = await PatentChunk.find({ 
        patentId, 
        embeddingStatus: { $ne: 'completed' } 
      }).sort({ chunkIndex: 1 });

      if (chunks.length === 0) return;

      await this._processBatches(chunks, 'patent');
    } catch (error) {
      console.error(`Failed to process patent embeddings for patent ${patentId}:`, error);
    }
  }

  /**
   * Internal method to handle batching and saving to ChromaDB
   * @param {Array} chunks 
   * @param {string} sourceType 'document' | 'patent'
   */
  async _processBatches(chunks, sourceType) {
    for (let i = 0; i < chunks.length; i += this.batchSize) {
      const batch = chunks.slice(i, i + this.batchSize);
      const texts = batch.map(c => c.text);
      const ids = batch.map(c => c._id.toString());
      
      const metadatas = batch.map(c => {
        const baseMeta = {
          sourceType,
          chunkIndex: c.chunkIndex,
        };
        if (sourceType === 'document') {
          baseMeta.projectId = c.projectId.toString();
        } else {
          baseMeta.patentId = c.patentId.toString();
        }
        return baseMeta;
      });

      try {
        // 1. Generate embeddings via the abstract provider
        const embeddings = await this.provider.generateEmbeddings(texts);

        // 2. Upsert to ChromaDB
        // Ensure all arrays have equal length before upsert
        const minLen = Math.min(ids.length, embeddings.length, metadatas.length, texts.length);
        const idsTrim = ids.slice(0, minLen);
        const embeddingsTrim = embeddings.slice(0, minLen);
        const metadatasTrim = metadatas.slice(0, minLen);
        const textsTrim = texts.slice(0, minLen);
        // Upsert with trimmed arrays
        await chromaService.upsertVectors(idsTrim, embeddingsTrim, metadatasTrim, textsTrim);

        // 3. Mark as completed in MongoDB
        const updatePromises = batch.map(c => {
          c.embeddingStatus = 'completed';
          return c.save();
        });
        await Promise.all(updatePromises);
        
      } catch (error) {
        console.error(`Error in batch ${i}-${i + this.batchSize}:`, error.message);
        // Mark as failed in MongoDB
        const failPromises = batch.map(c => {
          c.embeddingStatus = 'failed';
          return c.save();
        });
        await Promise.all(failPromises);
      }
    }
  }

  /**
   * Performs semantic search strictly on vectors (no reasoning/LLM)
   * @param {string} query 
   * @param {number} topK 
   */
  async searchSimilar(query, topK = 5) {
    // 1. Convert the query text into a vector using the exact same provider
    const [queryEmbedding] = await this.provider.generateEmbeddings([query]);
    
    // 2. Query ChromaDB for cosine similarity
    const results = await chromaService.querySimilar(queryEmbedding, topK);
    return results;
  }
}

module.exports = new EmbeddingService();
