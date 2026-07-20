const fs = require('fs');

class ReportFormatter {
  /**
   * Generates a raw JSON file dump.
   */
  async generateJsonReport(project, analysis, outputPath) {
    const data = {
      projectTitle: project.title,
      generatedAt: new Date().toISOString(),
      analysisId: analysis._id,
      scores: analysis.scores,
      detailedAnalysis: analysis.analysis
    };
    
    fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
    return outputPath;
  }

  /**
   * Generates a Markdown report.
   */
  async generateMarkdownReport(project, analysis, outputPath) {
    const data = analysis.analysis;
    const md = `# Patent Potential Analysis Report
**Project:** ${project.title}
**Date:** ${new Date().toLocaleDateString()}

## Executive Summary
${data.executiveSummary}

## Scores
- **Novelty:** ${data.noveltyScore}%
- **Similarity:** ${data.similarityScore}%
- **Innovation:** ${data.innovationScore}%
- **Confidence:** ${data.confidenceScore}%

## Recommendation
**${data.recommendation}**

## Unique Innovations
${data.uniqueInnovations ? data.uniqueInnovations.map(u => `- ${u}`).join('\n') : 'None'}

## Similar Patents
${data.similarPatents ? data.similarPatents.map(p => `- **${p.patentId}**: ${p.title} (Sim: ${p.similarity}%)\n  *Reason:* ${p.reason}`).join('\n') : 'None'}
`;
    fs.writeFileSync(outputPath, md);
    return outputPath;
  }
}

module.exports = new ReportFormatter();
