const analysisService = require('../services/analysisService');
const analysisRepository = require('../repositories/analysisRepository');

// @desc    Run Agentic RAG Analysis for a project
// @route   POST /api/analyze/:projectId
// @access  Private
const analyzeProject = async (req, res) => {
  try {
    const { projectId } = req.params;
    
    // Verify Ownership
    const Project = require('../models/Project');
    const project = await Project.findById(projectId);
    if (!project) return res.status(404).json({ success: false, message: 'Project not found' });
    if (project.user.toString() !== req.user._id.toString()) return res.status(403).json({ success: false, message: 'Not authorized' });

    // Trigger analysis
    const result = await analysisService.runAnalysis(projectId);

    res.status(200).json({
      success: true,
      message: 'Analysis completed successfully',
      data: result
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Analysis failed', error: error.message });
  }
};

// @desc    Get an existing analysis by project ID
// @route   GET /api/analyze/:projectId
// @access  Private
const getAnalysis = async (req, res) => {
  try {
    const { projectId } = req.params;
    
    // Verify Ownership
    const Project = require('../models/Project');
    const project = await Project.findById(projectId);
    if (!project) return res.status(404).json({ success: false, message: 'Project not found' });
    if (project.user.toString() !== req.user._id.toString()) return res.status(403).json({ success: false, message: 'Not authorized' });

    const analysis = await analysisRepository.getAnalysisByProjectId(projectId);

    if (!analysis) {
      return res.status(404).json({ success: false, message: 'Analysis not found for this project' });
    }

    res.status(200).json({
      success: true,
      message: 'Analysis retrieved successfully',
      data: analysis
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to retrieve analysis', error: error.message });
  }
};

module.exports = {
  analyzeProject,
  getAnalysis
};
