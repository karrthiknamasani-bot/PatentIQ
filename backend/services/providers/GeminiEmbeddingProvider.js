const { GoogleGenAI } = require('@google/genai');
const EmbeddingProvider = require('./EmbeddingProvider');

class GeminiEmbeddingProvider extends EmbeddingProvider {
  constructor(apiKey) {
    super();
    if (!apiKey) throw new Error("Gemini API Key is required");
    
    // Initialize the official Google Gen AI SDK client
    this.ai = new GoogleGenAI({ apiKey });
    this.modelName = 'gemini-embedding-2';
  }

  async generateEmbeddings(texts) {
    if (!texts || texts.length === 0) return [];
    
    // Mock logic for local testing without a real API key
    if (this.ai.apiKey === 'DUMMY_KEY_FOR_TESTING') {
      return texts.map(() => Array.from({ length: 3072 }, () => Math.random() - 0.5));
    }

    try {
      const response = await this.ai.models.embedContent({
        model: this.modelName,
        contents: texts
      });
      
      // The response.embeddings array matches the input order
      return response.embeddings.map(e => e.values);
    } catch (error) {
      console.error("Gemini Embedding Error:", error.message);
      throw error;
    }
  }

  getDimensions() {
    return 3072; // Standard output dimension for gemini-embedding-2
  }
}

module.exports = GeminiEmbeddingProvider;
