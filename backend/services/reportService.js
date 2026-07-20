const path = require('path');
const fs = require('fs');
const Project = require('../models/Project');
const Analysis = require('../models/Analysis');
const Report = require('../models/Report');
const pdfGenerator = require('./pdfGenerator');
const reportFormatter = require('./reportFormatter');

// Ensure reports directory exists
const reportsDir = path.join(__dirname, '../uploads/reports');
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

class ReportService {
  /**
   * Orchestrates generating a report.
   * @param {string} projectId 
   * @param {string} userId 
   * @param {string} reportType - 'pdf', 'json', 'markdown'
   */
  async generateReport(projectId, userId, reportType = 'pdf') {
    try {
      const project = await Project.findById(projectId);
      if (!project) throw new Error('Project not found');

      // Fetch the latest analysis for this project
      const analysis = await Analysis.findOne({ projectId }).sort({ createdAt: -1 });
      if (!analysis) throw new Error('No analysis found for this project. Please run Agentic RAG first.');

      const timestamp = Date.now();
      const fileName = `patentiq_report_${project._id}_${timestamp}.${reportType}`;
      const outputPath = path.join(reportsDir, fileName);

      // Create pending Report record in DB
      let report = new Report({
        projectId,
        analysisId: analysis._id,
        reportType,
        reportPath: outputPath,
        generatedBy: userId,
        status: 'pending'
      });
      await report.save();

      try {
        // Generate actual file
        if (reportType === 'pdf') {
          // Pass dummy user name for now, in a real app you'd fetch the User object
          await pdfGenerator.generateReport(project, analysis, outputPath, 'Authorized User');
        } else if (reportType === 'json') {
          await reportFormatter.generateJsonReport(project, analysis, outputPath);
        } else if (reportType === 'markdown') {
          await reportFormatter.generateMarkdownReport(project, analysis, outputPath);
        }

        report.status = 'completed';
        await report.save();
        return report;
      } catch (err) {
        report.status = 'failed';
        await report.save();
        throw new Error(`Failed to generate ${reportType.toUpperCase()} file: ${err.message}`);
      }

    } catch (error) {
      console.error("Report Generation Error:", error.message);
      throw error;
    }
  }

  /**
   * Retrieves report file path by ID
   */
  async getReportFilePath(reportId) {
    const report = await Report.findById(reportId);
    if (!report) throw new Error('Report not found');
    if (report.status !== 'completed') throw new Error('Report is not completed yet');
    if (!fs.existsSync(report.reportPath)) throw new Error('Report file is missing from disk');
    return report.reportPath;
  }
}

module.exports = new ReportService();
