const Analysis = require('../models/Analysis');
const Project = require('../models/Project');

class AnalysisRepository {
  /**
   * Save a completed analysis to the database and update the parent Project
   */
  async saveAnalysis(projectId, analysisData, modelUsed, processingTime, retrievedChunkCount, retrievedPatents) {
    try {
      const analysis = new Analysis({
        projectId,
        analysis: analysisData,
        scores: {
          noveltyScore: analysisData.noveltyScore || 0,
          similarityScore: analysisData.similarityScore || 0,
          innovationScore: analysisData.patentPotentialScore || 0,
          confidenceScore: analysisData.confidence || 0,
        },
        modelUsed,
        processingTime,
        retrievedChunkCount,
        retrievedPatents,
        status: 'completed'
      });

      await analysis.save();

      // Update the parent project with the high-level scores
      await Project.findByIdAndUpdate(projectId, {
        patentPotentialScore: analysisData.patentPotentialScore || 0,
        noveltyScore: analysisData.noveltyScore || 0,
        similarityScore: analysisData.similarityScore || 0,
        aiSummary: analysisData.innovationSummary || ''
      });

      return analysis;
    } catch (error) {
      console.error("Error saving analysis to DB:", error);
      throw error;
    }
  }

  async getAnalysisByProjectId(projectId) {
    return await Analysis.findOne({ projectId }).sort({ createdAt: -1 });
  }
}

module.exports = new AnalysisRepository();
