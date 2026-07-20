const chromaService = require('./chromaService');
const DocumentChunk = require('../models/DocumentChunk');

class RagService {
  /**
   * Performs the retrieval step of Agentic RAG.
   * Finds the most relevant patent chunks for a given project.
   * 
   * @param {string} projectId 
   * @param {number} topK 
   * @returns {Promise<Array>} Array of top-k unique and sorted patent chunks
   */
  async retrieveRelevantPatents(projectId, topK = 15) {
    // 1. Fetch user document chunks from MongoDB to get their IDs
    const projectChunks = await DocumentChunk.find({ projectId }).sort({ chunkIndex: 1 });
    
    if (!projectChunks || projectChunks.length === 0) {
      throw new Error("No processed document chunks found for this project. Ensure processing & embeddings are complete.");
    }

    const chunkIds = projectChunks.map(c => c._id.toString());

    // 2. Fetch the actual embeddings for these chunks from ChromaDB
    const collection = await chromaService.init();
    const userVectorsResponse = await collection.get({
      ids: chunkIds,
      include: ['embeddings', 'documents', 'metadatas']
    });

    if (!userVectorsResponse.embeddings || userVectorsResponse.embeddings.length === 0) {
       throw new Error("Embeddings not found in ChromaDB. Ensure Phase 6 completed successfully.");
    }

    const userEmbeddings = userVectorsResponse.embeddings;

    // 3. Parallel Retrieval: Query ChromaDB for similar patent chunks using EACH user chunk
    // We only want to search against patents, not other user documents.
    const searchPromises = userEmbeddings.map(embedding => 
      chromaService.querySimilar(embedding, 5, { sourceType: 'patent' })
    );

    const searchResults = await Promise.all(searchPromises);

    // 4. Flatten, deduplicate, and rank
    const patentMap = new Map();

    // ChromaDB returns distances (lower is better for cosine distance in Chroma depending on metric)
    searchResults.forEach((resultBlock) => {
      if (!resultBlock.ids || resultBlock.ids.length === 0) return;
      
      const ids = resultBlock.ids[0];
      const distances = resultBlock.distances[0];
      const metadatas = resultBlock.metadatas[0];
      const documents = resultBlock.documents[0];

      for (let i = 0; i < ids.length; i++) {
        const id = ids[i];
        const dist = distances[i];
        
        // Convert distance to similarity score (0 to 1) for easier downstream logic
        // Assuming cosine distance (0 is exact match, 2 is opposite). Sim = 1 - (dist/2)
        const simScore = 1 - (dist / 2);

        if (!patentMap.has(id)) {
          patentMap.set(id, {
            id,
            text: documents[i],
            metadata: metadatas[i],
            similarity: simScore
          });
        } else {
          // If we found the same chunk again, keep the higher similarity score
          if (simScore > patentMap.get(id).similarity) {
            patentMap.get(id).similarity = simScore;
          }
        }
      }
    });

    // Convert map to array and sort by similarity descending
    const sortedPatents = Array.from(patentMap.values()).sort((a, b) => b.similarity - a.similarity);

    // Grouping neighboring chunks from the same patent (simplistic merge)
    // To keep it clean and token-friendly, we simply take the top K.
    // If multiple top K belong to the same patent, promptBuilder will format them cleanly.
    
    return sortedPatents.slice(0, topK);
  }
}

module.exports = new RagService();
