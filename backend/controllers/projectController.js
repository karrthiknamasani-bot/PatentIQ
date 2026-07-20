const Project = require('../models/Project');
const DocumentChunk = require('../models/DocumentChunk');
const Analysis = require('../models/Analysis');
const Report = require('../models/Report');
const fs = require('fs');
const { startBackgroundPipeline } = require('./processController');

// @desc    Upload a project document
// @route   POST /api/projects/upload
// @access  Private
const uploadProject = async (req, res) => {
  try {
    const { title, description } = req.body;
    const file = req.file;

    const errors = [];
    if (!title || title.trim() === '') errors.push('Title is required');
    if (!file) errors.push('Document file is required');

    if (errors.length > 0) {
      if (file && fs.existsSync(file.path)) fs.unlinkSync(file.path);
      return res.status(400).json({ success: false, message: 'Validation failed', errors });
    }

    const project = await Project.create({
      user: req.user._id,
      title,
      description: description || '',
      originalFileName: file.originalname,
      storedFileName: file.filename,
      filePath: file.path,
      fileType: file.mimetype,
      fileSize: file.size,
      status: 'processing',
      processingStage: 'queued',
      progress: 5,
      processingStartedAt: new Date()
    });

    // Start background processing pipeline
    setTimeout(() => {
      startBackgroundPipeline(project._id);
    }, 0);

    res.status(201).json({
      success: true,
      message: 'Project uploaded successfully',
      data: project
    });
  } catch (error) {
    if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

// @desc    Get all projects for logged in user
// @route   GET /api/projects
// @access  Private
const getProjects = async (req, res) => {
  try {
    const projects = await Project.find({ user: req.user._id }).sort({ createdAt: -1 });
    res.status(200).json({
      success: true,
      message: 'Projects retrieved successfully',
      data: projects
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

// @desc    Get specific project by ID
// @route   GET /api/projects/:id
// @access  Private
const getProjectById = async (req, res) => {
  try {
    const project = await Project.findById(req.params.id);

    if (!project) {
      return res.status(404).json({ success: false, message: 'Project not found', errors: [] });
    }

    if (project.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ success: false, message: 'Not authorized to access this project', errors: [] });
    }

    res.status(200).json({
      success: true,
      message: 'Project retrieved successfully',
      data: project
    });
  } catch (error) {
    if (error.kind === 'ObjectId') {
      return res.status(400).json({ success: false, message: 'Invalid Project ID format', errors: [] });
    }
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

// @desc    Delete a project
// @route   DELETE /api/projects/:id
// @access  Private
const deleteProject = async (req, res) => {
  try {
    const project = await Project.findById(req.params.id);

    if (!project) {
      return res.status(404).json({ success: false, message: 'Project not found', errors: [] });
    }

    if (project.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ success: false, message: 'Not authorized to delete this project', errors: [] });
    }

    // Delete file from disk
    if (project.filePath && fs.existsSync(project.filePath)) {
      fs.unlinkSync(project.filePath);
    }

    // Cascade delete Document Chunks
    await DocumentChunk.deleteMany({ projectId: project._id });

    // Cascade delete Analysis
    await Analysis.deleteMany({ projectId: project._id });

    // Cascade delete Reports and their physical files
    const reports = await Report.find({ projectId: project._id });
    for (const report of reports) {
      if (report.reportPath && fs.existsSync(report.reportPath)) {
        fs.unlinkSync(report.reportPath);
      }
    }
    await Report.deleteMany({ projectId: project._id });

    await project.deleteOne();

    res.status(200).json({
      success: true,
      message: 'Project deleted successfully',
      data: {}
    });
  } catch (error) {
    if (error.kind === 'ObjectId') {
      return res.status(400).json({ success: false, message: 'Invalid Project ID format', errors: [] });
    }
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

module.exports = {
  uploadProject,
  getProjects,
  getProjectById,
  deleteProject
};
