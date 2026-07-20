const fs = require('fs');
const pdfParse = require('pdf-parse');
const mammoth = require('mammoth');

/**
 * Parses a document based on its mime type or extension and extracts raw text.
 * @param {string} filePath 
 * @param {string} fileType 
 * @returns {object} { text, metadata, parserUsed }
 */
const parseDocument = async (filePath, fileType) => {
  if (!fs.existsSync(filePath)) {
    throw new Error('File not found on disk');
  }

  const fileBuffer = fs.readFileSync(filePath);
  
  // PDF Parsing
  if (fileType === 'application/pdf' || filePath.toLowerCase().endsWith('.pdf')) {
    const data = await pdfParse(fileBuffer);
    return {
      text: data.text,
      metadata: data.info || { numpages: data.numpages },
      parserUsed: 'pdf-parse'
    };
  }
  
  // DOCX Parsing
  if (fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || filePath.toLowerCase().endsWith('.docx')) {
    const result = await mammoth.extractRawText({ buffer: fileBuffer });
    return {
      text: result.value,
      metadata: {},
      parserUsed: 'mammoth'
    };
  }
  
  // TXT Parsing
  if (fileType === 'text/plain' || filePath.toLowerCase().endsWith('.txt')) {
    const text = fileBuffer.toString('utf-8');
    return {
      text,
      metadata: {},
      parserUsed: 'fs.readFileSync'
    };
  }

  throw new Error(`Unsupported file type for parsing: ${fileType}`);
};

module.exports = {
  parseDocument
};
