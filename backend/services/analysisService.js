const Project = require('../models/Project');
const DocumentChunk = require('../models/DocumentChunk');
const ragService = require('./ragService');
const geminiService = require('./geminiService');
const analysisRepository = require('../repositories/analysisRepository');

class AnalysisService {
  /**
   * Orchestrates the complete Agentic RAG flow
   * @param {string} projectId 
   */
  async runAnalysis(projectId) {
    const startTime = Date.now();
    console.log(`[Analysis] Starting analysis for project: ${projectId}`);

    try {
      // 1. Load Project
      const project = await Project.findById(projectId);
      if (!project) throw new Error('Project not found');

      if (project.status !== 'processed') {
        throw new Error('Project must be fully processed before analysis.');
      }

      // 2. Fetch full project text by merging its chunks (for the prompt context)
      const projectChunks = await DocumentChunk.find({ projectId }).sort({ chunkIndex: 1 });
      const projectFullText = projectChunks.map(c => c.text).join('\n\n');

      // 3. Retrieve Top-K Similar Patent Chunks
      console.log(`[Analysis] Retrieving vectors from ChromaDB...`);
      const retrievedPatents = await ragService.retrieveRelevantPatents(projectId, 15);

      // 4. Call Gemini 2.5 Flash via Gemini Service
      const parsedJson = await geminiService.generateStructuredAnalysis(project.title, projectFullText, retrievedPatents);

      // 5. Save Analysis
      console.log(`[Analysis] Saving structured analysis to MongoDB...`);
      const processingTime = Date.now() - startTime;
      
      const analysisRecord = await analysisRepository.saveAnalysis(
        projectId,
        parsedJson,
        `gemini-embedding-2 + gemini-3.1-flash-lite`,
        processingTime,
        retrievedPatents.length,
        retrievedPatents.map(p => p.metadata.patentId || 'Unknown_Patent')
      );

      console.log(`[Analysis] Completed successfully in ${processingTime}ms`);
      return analysisRecord;

    } catch (error) {
      console.error(`[Analysis] Fatal Error:`, error.message);
      
      // Update project status if something catastrophic failed
      await Project.findByIdAndUpdate(projectId, {
         processingStage: 'failed_analysis'
      });
      
      throw error;
    }
  }
}

module.exports = new AnalysisService();
