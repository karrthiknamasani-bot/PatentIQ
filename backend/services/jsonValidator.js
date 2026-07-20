class JsonValidator {
  /**
   * Cleans and parses a raw string response into JSON.
   * Handles markdown wrappers (```json ... ```) and ensures schema compliance.
   * @param {string} rawString 
   * @returns {Object} Parsed JSON Object
   * @throws {Error} If invalid JSON or missing critical schema fields
   */
  validateAndParse(rawString) {
    let cleanString = rawString.trim();

    // Remove markdown json formatting if it exists
    if (cleanString.startsWith('```json')) {
      cleanString = cleanString.replace(/^```json/, '');
    }
    if (cleanString.startsWith('```')) {
      cleanString = cleanString.replace(/^```/, '');
    }
    if (cleanString.endsWith('```')) {
      cleanString = cleanString.replace(/```$/, '');
    }
    
    cleanString = cleanString.trim();

    let parsed;
    try {
      parsed = JSON.parse(cleanString);
    } catch (error) {
      throw new Error(`Failed to parse JSON string: ${error.message}`);
    }

    // Basic Schema Validation
    const requiredKeys = [
      'executiveSummary', 
      'noveltyScore', 
      'similarityScore', 
      'innovationScore',
      'confidenceScore',
      'recommendation',
      'technicalAnalysis',
      'similarPatents',
      'uniqueInnovations',
      'potentialRisks',
      'improvementSuggestions',
      'references'
    ];

    for (const key of requiredKeys) {
      if (parsed[key] === undefined) {
        throw new Error(`Parsed JSON is missing required schema key: '${key}'`);
      }
    }

    return parsed;
  }
}

module.exports = new JsonValidator();
