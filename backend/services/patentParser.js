const fs = require('fs');
const csv = require('csv-parser');

/**
 * Parses a JSON or CSV file containing patent data.
 * @param {string} filePath 
 * @param {string} mimetype 
 * @returns {Promise<Array>} Array of patent objects
 */
const parsePatentFile = (filePath, mimetype) => {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(filePath)) {
      return reject(new Error('File not found'));
    }

    const patents = [];
    const ext = filePath.split('.').pop().toLowerCase();

    if (mimetype === 'application/json' || ext === 'json') {
      try {
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const data = JSON.parse(fileContent);
        // Ensure it's an array
        const patentArray = Array.isArray(data) ? data : (data.patents || [data]);
        resolve(patentArray);
      } catch (err) {
        reject(new Error(`Failed to parse JSON: ${err.message}`));
      }
    } else if (mimetype === 'text/csv' || ext === 'csv') {
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (row) => {
          // Normalize row keys to map to Patent schema if possible
          // Expected CSV headers: patentNumber, title, abstract, inventors, assignee, publicationDate, ipcClasses, source
          const patent = {
            patentNumber: row.patentNumber || row.id || '',
            title: row.title || '',
            abstract: row.abstract || '',
            inventors: row.inventors ? row.inventors.split(';').map(i => i.trim()) : [],
            assignee: row.assignee || '',
            publicationDate: row.publicationDate ? new Date(row.publicationDate) : null,
            ipcClasses: row.ipcClasses ? row.ipcClasses.split(';').map(i => i.trim()) : [],
            source: row.source || 'custom',
            metadata: row.metadata ? JSON.parse(row.metadata) : {}
          };
          patents.push(patent);
        })
        .on('end', () => resolve(patents))
        .on('error', (err) => reject(new Error(`Failed to parse CSV: ${err.message}`)));
    } else if (ext === 'xml') {
      // Future-ready scaffolding for XML
      reject(new Error('XML parsing is planned for a future release'));
    } else {
      reject(new Error('Unsupported file type for patent import. Please use JSON or CSV.'));
    }
  });
};

module.exports = {
  parsePatentFile
};
