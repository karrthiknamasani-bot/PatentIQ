/**
 * Chunks a large text document into smaller overlapping segments.
 * @param {string} text 
 * @param {mongoose.Types.ObjectId} projectId 
 * @param {number} chunkSize 
 * @param {number} overlap 
 * @returns {Array} Array of chunk objects ready to be saved to DB
 */
const chunkText = (text, projectId, chunkSize = 1000, overlap = 200) => {
  if (!text) return [];
  
  const chunks = [];
  let startIndex = 0;
  let chunkIndex = 0;
  const textLength = text.length;

  while (startIndex < textLength) {
    let endIndex = startIndex + chunkSize;

    // If we're not at the end of the text, try to snap to the nearest space or newline 
    // to avoid cutting words in half.
    if (endIndex < textLength) {
      // Find the last space or newline before the cutoff
      let snapIndex = text.lastIndexOf(' ', endIndex);
      let newlineIndex = text.lastIndexOf('\n', endIndex);
      
      // Use newline if it's within the last 100 chars of the chunk, else space
      if (newlineIndex > endIndex - 100 && newlineIndex > startIndex) {
        endIndex = newlineIndex;
      } else if (snapIndex > startIndex) {
        endIndex = snapIndex;
      }
    } else {
      endIndex = textLength;
    }

    const chunkText = text.substring(startIndex, endIndex).trim();
    
    if (chunkText.length > 0) {
      chunks.push({
        projectId,
        chunkIndex,
        text: chunkText,
        startCharacter: startIndex,
        endCharacter: endIndex,
        // Rough estimate: 1 token ≈ 4 characters
        tokenEstimate: Math.ceil(chunkText.length / 4)
      });
      chunkIndex++;
    }

    // Move start index forward, accounting for overlap
    const nextStartIndex = endIndex - overlap;
    
    // Prevent infinite loop if snapIndex caused us to go backwards or stall
    if (nextStartIndex <= startIndex) {
      startIndex += (chunkSize - overlap); // Force progress forward
    } else {
      startIndex = nextStartIndex;
    }
  }

  return chunks;
};

module.exports = {
  chunkText
};
