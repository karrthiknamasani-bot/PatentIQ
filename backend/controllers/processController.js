const Project = require('../models/Project');
const DocumentChunk = require('../models/DocumentChunk');
const { parseDocument } = require('../services/documentParser');
const { cleanText } = require('../services/textCleaner');
const { chunkText } = require('../services/textChunker');
const embeddingService = require('../services/embeddingService');
const analysisService = require('../services/analysisService');
const { extractMetadata } = require('../services/metadataExtractor');

const updateProjectProgress = async (project, stage, progressPercentage, status = 'processing') => {
  project.processingStage = stage;
  project.progress = progressPercentage;
  project.status = status;
  await project.save();
};

const startBackgroundPipeline = async (projectId) => {
  try {
    const project = await Project.findById(projectId);
    if (!project) return;
    
    await updateProjectProgress(project, 'parsing', 15);
    
    // 1. Parse Document
    const { text, metadata, parserUsed } = await parseDocument(project.filePath, project.fileType);
    console.log('✓ Parsing Complete');

    // 2. Clean Text
    await updateProjectProgress(project, 'cleaning', 25);
    const cleanedText = cleanText(text);
    
    if (cleanedText.length === 0) {
      throw new Error('Parsed document is empty or unreadable');
    }

    // 3. Extract Metadata
    const finalMetadata = extractMetadata(cleanedText, metadata, parserUsed);

    // 4. Chunk Document
    await updateProjectProgress(project, 'chunking', 40);
    
    // Remove old chunks if this is a retry
    await DocumentChunk.deleteMany({ projectId: project._id });
    
    const chunks = chunkText(cleanedText, project._id, 1000, 200);
    await DocumentChunk.insertMany(chunks);
    console.log('✓ Chunking Complete');

    // 5. Generate Embeddings (Await it now!)
    await updateProjectProgress(project, 'embedding', 60);
    await embeddingService.processProjectEmbeddings(project._id);
    console.log('✓ Embeddings Complete');

    // ** CRITICAL FIX: Set status to processed BEFORE analysis **
    await updateProjectProgress(project, 'processed', 75, 'processed');
    console.log('✓ Status Updated -> processed');

    // 6. Retrieval & Gemini Analysis
    console.log('✓ Starting Analysis');
    project.status = 'processed';
    project.processingStage = 'processed';
    project.progress = 90;
    await project.save();
    
    const analysisRecord = await analysisService.runAnalysis(project._id);
    console.log('✓ Analysis Complete');

    // 7. Finalize Updates
    const analysisData = analysisRecord.analysis;
    
    project.technicalDomain = analysisData.technicalDomain;
    project.innovationSummary = analysisData.innovationSummary;
    project.patentPotentialScore = analysisData.patentPotentialScore;
    project.noveltyScore = analysisData.noveltyScore;
    project.similarityScore = analysisData.similarityScore;
    project.strengths = analysisData.strengths || [];
    project.weaknesses = analysisData.weaknesses || [];
    project.commercialApplications = analysisData.commercialApplications || [];
    project.recommendation = analysisData.recommendation;
    project.confidence = analysisData.confidence;
    
    project.analysisModel = analysisRecord.modelUsed;
    project.analysisTimestamp = new Date();
    project.aiSummary = analysisData.innovationSummary;
    project.reportGenerated = true;

    project.extractedText = cleanedText;
    project.extractedMetadata = finalMetadata;
    project.processingCompletedAt = new Date();
    project.processingDuration = project.processingCompletedAt - project.processingStartedAt;
    project.errorMessage = null;
    project.processingError = null;
    
    await updateProjectProgress(project, 'completed', 100, 'completed');
    console.log('✓ Report Saved');

  } catch (err) {
    console.error('Processing failed:', err);
    try {
      const failedProject = await Project.findById(projectId);
      if (failedProject) {
        failedProject.status = 'failed';
        failedProject.processingError = err.message;
        failedProject.errorMessage = err.message;
        failedProject.processingCompletedAt = new Date();
        await failedProject.save();
      }
    } catch (saveErr) {
      console.error('Failed to save error state to project:', saveErr);
    }
  }
};

// @desc    Process a document (parse, clean, chunk) - Manual Retry Endpoint
// @route   POST /api/process/:projectId
// @access  Private
const processDocument = async (req, res) => {
  const { projectId } = req.params;
  
  try {
    const project = await Project.findById(projectId);
    
    if (!project) {
      return res.status(404).json({ success: false, message: 'Project not found', errors: [] });
    }
    
    if (project.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ success: false, message: 'Not authorized', errors: [] });
    }

    // Update status to processing
    project.status = 'processing';
    project.processingStage = 'queued';
    project.progress = 5;
    project.processingStartedAt = new Date();
    await project.save();

    res.status(202).json({ success: true, message: 'Document processing queued', data: { projectId } });

    // --- BACKGROUND PROCESSING ---
    setTimeout(() => {
      startBackgroundPipeline(projectId);
    }, 0);

  } catch (error) {
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

// @desc    Get processing status
// @route   GET /api/process/:projectId/status
// @access  Private
const getProcessingStatus = async (req, res) => {
  try {
    const project = await Project.findById(req.params.projectId).select('status processingStage progress processingStartedAt processingCompletedAt processingDuration errorMessage processingError patentPotentialScore noveltyScore similarityScore reportGenerated aiSummary');
    
    if (!project) {
      return res.status(404).json({ success: false, message: 'Project not found', errors: [] });
    }
    
    res.status(200).json({ success: true, message: 'Status retrieved', data: project });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

module.exports = {
  processDocument,
  getProcessingStatus,
  startBackgroundPipeline
};
