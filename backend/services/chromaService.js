const { ChromaClient } = require('chromadb');

class ChromaService {
  constructor() {
    this.client = new ChromaClient({ path: "http://localhost:8000" });
    this.collectionName = 'patentiq_vectors';
    this.collection = null;
  }

  async init() {
    if (this.collection) return this.collection;
    
    try {
      // Get or create the unified vector collection
      this.collection = await this.client.getOrCreateCollection({
        name: this.collectionName,
        metadata: { "description": "Unified PatentIQ Vectors (Projects & Patents)" },
        embeddingFunction: {
          generate: async (texts) => []
        }
      });
      console.log(`ChromaDB Collection initialized: ${this.collectionName}`);
      return this.collection;
    } catch (error) {
      console.error("ChromaDB Initialization Error:", error.message);
      throw error;
    }
  }

  /**
   * Upserts vectors into ChromaDB.
   * @param {string[]} ids - Array of unique string IDs (e.g., chunk._id.toString())
   * @param {Array<Array<number>>} embeddings - Array of vector arrays
   * @param {Array<Object>} metadatas - Array of metadata objects for each chunk
   * @param {string[]} documents - Array of raw text strings for each chunk
   */
  async upsertVectors(ids, embeddings, metadatas, documents) {
    if (!this.collection) await this.init();
    
    try {
      console.log('Upsert arrays lengths -> ids:', ids.length, 'embeddings:', embeddings.length, 'metadatas:', metadatas.length, 'documents:', documents.length);
      console.log('Sample id:', ids[0], 'sample meta:', metadatas[0]);
      await this.collection.upsert({
        ids,
        embeddings,
        metadatas,
        documents
      });
    } catch (error) {
      console.error("ChromaDB Upsert Error:", error.message);
      throw error;
    }
  }

  /**
   * Queries the ChromaDB for semantic similarity
   * @param {Array<number>} queryEmbedding - The embedding vector of the search query
   * @param {number} nResults - Number of results to return
   * @param {Object} where - Optional metadata filter (e.g., { sourceType: 'patent' })
   */
  async querySimilar(queryEmbedding, nResults = 5, where = undefined) {
    if (!this.collection) await this.init();
    
    try {
      const results = await this.collection.query({
        queryEmbeddings: [queryEmbedding],
        nResults,
        where
      });
      return results;
    } catch (error) {
      console.error("ChromaDB Query Error:", error.message);
      throw error;
    }
  }
}

// Export as a singleton
module.exports = new ChromaService();
