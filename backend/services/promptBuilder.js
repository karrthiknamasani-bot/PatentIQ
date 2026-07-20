class PromptBuilder {
  /**
   * Constructs the structured prompt for the Gemini Agentic Reasoning phase.
   * @param {string} projectTitle 
   * @param {string} projectFullText 
   * @param {Array} retrievedPatents 
   * @returns {string} The formatted prompt string
   */
  buildAnalysisPrompt(projectTitle, projectFullText, retrievedPatents) {
    let priorArtContext = "=== RELEVANT PRIOR ART FINDINGS ===\n\n";
    
    if (retrievedPatents.length === 0) {
      priorArtContext += "No relevant prior art was found in the database.\n\n";
    } else {
      const patentGroups = {};
      retrievedPatents.forEach(p => {
        const pId = p.metadata.patentId || 'Unknown_Patent';
        if (!patentGroups[pId]) patentGroups[pId] = [];
        patentGroups[pId].push(p);
      });

      for (const [pId, chunks] of Object.entries(patentGroups)) {
        priorArtContext += `--- Patent ID: ${pId} ---\n`;
        chunks.forEach((chunk, idx) => {
          priorArtContext += `Chunk ${idx + 1} (Similarity: ${(chunk.similarity * 100).toFixed(1)}%):\n"${chunk.text}"\n\n`;
        });
      }
    }

    const truncatedProjectText = projectFullText.length > 100000 
      ? projectFullText.substring(0, 100000) + "...[TRUNCATED]" 
      : projectFullText;

    const projectContext = `=== USER PROJECT ===\nTitle: ${projectTitle}\n\nProject Description/Text:\n${truncatedProjectText}\n\n`;

    const instructions = `
You are an experienced patent examiner.
Your task is to analyze the uploaded invention using ONLY the supplied document and retrieved technical context.

Do not invent facts.
If information is insufficient, explicitly state it.

Evaluate:
1. Technical Domain
2. Innovation Summary
3. Novelty Score (0-100)
4. Similarity Score (0-100)
5. Patent Potential Score (0-100)
6. Strengths
7. Weaknesses
8. Commercial Applications
9. Patent Filing Recommendation
10. Confidence Score (Based on the retrieved context)

You MUST return your ENTIRE response as a strictly valid JSON object matching the exact schema below.
DO NOT use markdown formatting like \`\`\`json. Return pure JSON.
No prose outside the JSON.

SCHEMA:
{
  "technicalDomain": "string",
  "innovationSummary": "string",
  "noveltyScore": 0,
  "similarityScore": 0,
  "patentPotentialScore": 0,
  "strengths": ["string", "string"],
  "weaknesses": ["string", "string"],
  "commercialApplications": ["string", "string"],
  "recommendation": "string",
  "confidence": 0
}
`;

    return `${instructions}\n\n${projectContext}\n\n${priorArtContext}`;
  }
}

module.exports = new PromptBuilder();
