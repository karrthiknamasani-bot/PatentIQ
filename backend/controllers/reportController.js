const path = require('path');
const reportService = require('../services/reportService');
const Report = require('../models/Report');

// @desc    Generate a new report for a project
// @route   POST /api/report/:projectId
// @access  Private
const generateReport = async (req, res) => {
  try {
    const { projectId } = req.params;
    const { type } = req.body; // 'pdf', 'json', 'markdown' (default 'pdf')
    const userId = req.user._id;

    // Verify Ownership
    const Project = require('../models/Project');
    const project = await Project.findById(projectId);
    if (!project) return res.status(404).json({ success: false, message: 'Project not found' });
    if (project.user.toString() !== userId.toString()) return res.status(403).json({ success: false, message: 'Not authorized' });

    const reportType = type || 'pdf';
    
    // Validate type
    if (!['pdf', 'json', 'markdown'].includes(reportType)) {
      return res.status(400).json({ success: false, message: 'Invalid report type' });
    }

    const report = await reportService.generateReport(projectId, userId, reportType);

    res.status(201).json({
      success: true,
      message: `${reportType.toUpperCase()} Report generated successfully`,
      data: report
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to generate report', error: error.message });
  }
};

// @desc    Download a generated report
// @route   GET /api/report/:reportId
// @access  Private
const downloadReport = async (req, res) => {
  try {
    const { reportId } = req.params;
    const userId = req.user._id;
    
    const report = await Report.findById(reportId).populate('projectId');
    if (!report) return res.status(404).json({ success: false, message: 'Report not found' });
    if (report.projectId.user.toString() !== userId.toString()) return res.status(403).json({ success: false, message: 'Not authorized' });
    
    const filePath = await reportService.getReportFilePath(reportId);
    const fileName = path.basename(filePath);

    res.download(filePath, fileName, (err) => {
      if (err) {
        console.error("Error downloading file:", err);
        // Only send response if headers haven't been sent yet
        if (!res.headersSent) {
          res.status(500).json({ success: false, message: 'Error downloading file' });
        }
      }
    });
  } catch (error) {
    res.status(404).json({ success: false, message: error.message });
  }
};

// @desc    Get report history for a project
// @route   GET /api/report/project/:projectId
// @access  Private
const getProjectReports = async (req, res) => {
  try {
    const { projectId } = req.params;
    const userId = req.user._id;

    // Verify Ownership
    const Project = require('../models/Project');
    const project = await Project.findById(projectId);
    if (!project) return res.status(404).json({ success: false, message: 'Project not found' });
    if (project.user.toString() !== userId.toString()) return res.status(403).json({ success: false, message: 'Not authorized' });
    
    const reports = await Report.find({ projectId }).sort({ createdAt: -1 });

    res.status(200).json({
      success: true,
      data: reports
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to fetch report history', error: error.message });
  }
};

module.exports = {
  generateReport,
  downloadReport,
  getProjectReports
};
