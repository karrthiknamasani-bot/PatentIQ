const Patent = require('../models/Patent');
const PatentChunk = require('../models/PatentChunk');
const { parsePatentFile } = require('./patentParser');
const { cleanText } = require('./textCleaner');
const { chunkText } = require('./textChunker');
const embeddingService = require('./embeddingService');

/**
 * Orchestrates the importing, cleaning, chunking, and saving of patents.
 * @param {string} filePath 
 * @param {string} mimetype 
 * @returns {object} Summary of imported patents
 */
const importPatents = async (filePath, mimetype) => {
  const rawPatents = await parsePatentFile(filePath, mimetype);
  
  if (!rawPatents || rawPatents.length === 0) {
    throw new Error('No valid patents found in the file');
  }

  let successCount = 0;
  let failedCount = 0;
  const errors = [];

  for (const raw of rawPatents) {
    try {
      // 1. Validate basic fields
      if (!raw.patentNumber || !raw.title || !raw.abstract) {
        throw new Error(`Missing required fields for patent: ${raw.patentNumber || 'UNKNOWN'}`);
      }

      // 2. Check if it already exists (upsert logic)
      let patent = await Patent.findOne({ patentNumber: raw.patentNumber });
      
      if (!patent) {
        patent = new Patent({
          patentNumber: raw.patentNumber,
          title: raw.title,
          abstract: raw.abstract,
          inventors: raw.inventors || [],
          assignee: raw.assignee || '',
          publicationDate: raw.publicationDate || null,
          ipcClasses: raw.ipcClasses || [],
          source: raw.source || 'custom',
          metadata: raw.metadata || {}
        });
        await patent.save();
      } else {
        // If updating an existing patent, we might want to clear old chunks
        await PatentChunk.deleteMany({ patentId: patent._id });
      }

      // 3. Clean Text (Combine Title + Abstract for searchability)
      const combinedText = `${raw.title}\n\n${raw.abstract}`;
      const cleaned = cleanText(combinedText);

      // 4. Chunk Document (using the generic textChunker)
      // We pass 1000 size, 200 overlap. 
      const rawChunks = chunkText(cleaned, patent._id, 1000, 200);

      // Map raw chunks to the PatentChunk schema format
      const patentChunks = rawChunks.map(c => ({
        patentId: c.projectId, // the textChunker calls it projectId, we remap it
        chunkIndex: c.chunkIndex,
        text: c.text,
        metadata: {
          startCharacter: c.startCharacter,
          endCharacter: c.endCharacter,
          tokenEstimate: c.tokenEstimate
        }
      }));

      // 5. Save Chunks
      if (patentChunks.length > 0) {
        await PatentChunk.insertMany(patentChunks);
        
        // Fire off embedding generation asynchronously
        embeddingService.processPatentEmbeddings(patent._id);
      }

      successCount++;
    } catch (err) {
      failedCount++;
      errors.push(`Patent ${raw.patentNumber || 'UNKNOWN'}: ${err.message}`);
    }
  }

  return {
    totalProcessed: rawPatents.length,
    successCount,
    failedCount,
    errors: errors.slice(0, 10) // Only return first 10 errors to avoid massive payload
  };
};

module.exports = {
  importPatents
};
