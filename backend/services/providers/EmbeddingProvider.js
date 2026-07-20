/**
 * Abstract Base Class for Embedding Providers
 * This enforces a strict contract so the system remains provider-agnostic.
 * Any embedding model (OpenAI, Gemini, HuggingFace) can be swapped in
 * as long as it extends this class and implements `generateEmbeddings`.
 */
class EmbeddingProvider {
  /**
   * Initializes the provider with required credentials.
   * @param {Object} config 
   */
  constructor(config) {
    if (new.target === EmbeddingProvider) {
      throw new TypeError("Cannot construct EmbeddingProvider instances directly");
    }
  }

  /**
   * Generates vector embeddings for a given array of texts.
   * @param {string[]} texts - Array of text strings to embed.
   * @returns {Promise<Array<Array<number>>>} - Promise resolving to an array of vector arrays.
   */
  async generateEmbeddings(texts) {
    throw new Error('Method generateEmbeddings() must be implemented.');
  }

  /**
   * Return the dimensionality of the vectors produced by this model.
   * @returns {number}
   */
  getDimensions() {
    throw new Error('Method getDimensions() must be implemented.');
  }
}

module.exports = EmbeddingProvider;
