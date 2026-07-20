/**
 * Extracts standard metadata from the cleaned text and raw parser output.
 * @param {string} cleanedText 
 * @param {object} parserMetadata (e.g., from pdf-parse)
 * @param {string} parserUsed 
 * @returns {object} metadata
 */
const extractMetadata = (cleanedText, parserMetadata, parserUsed) => {
  const wordCount = cleanedText.split(/\s+/).filter(word => word.length > 0).length;
  const characterCount = cleanedText.length;

  return {
    title: parserMetadata.title || 'Untitled Document',
    totalPages: parserMetadata.numpages || 1,
    totalWords: wordCount,
    totalCharacters: characterCount,
    detectedLanguage: 'en', // Can be upgraded with franc or cld3 later
    parserUsed: parserUsed,
    extractedAt: new Date().toISOString()
  };
};

module.exports = {
  extractMetadata
};
