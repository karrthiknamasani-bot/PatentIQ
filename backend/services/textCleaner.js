/**
 * Cleans extracted text to ensure consistent formatting for chunking and embeddings.
 * @param {string} rawText 
 * @returns {string} cleanedText
 */
const cleanText = (rawText) => {
  if (!rawText) return '';

  return rawText
    // Remove null bytes
    .replace(/\0/g, '')
    // Normalize unicode characters (e.g. smart quotes, em dashes)
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2013\u2014]/g, "-")
    // Replace multiple spaces with a single space (while keeping newlines intact)
    .replace(/[ \t]+/g, ' ')
    // Replace 3+ consecutive newlines with exactly 2 newlines (preserves paragraph structure)
    .replace(/\n{3,}/g, '\n\n')
    // Trim leading and trailing whitespace from each line
    .split('\n')
    .map(line => line.trim())
    .join('\n')
    // Final trim of the entire document
    .trim();
};

module.exports = {
  cleanText
};
