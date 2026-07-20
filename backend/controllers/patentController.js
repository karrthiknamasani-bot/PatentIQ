const fs = require('fs');
const Patent = require('../models/Patent');
const PatentChunk = require('../models/PatentChunk');
const { importPatents } = require('../services/patentImporter');

// @desc    Import patents from a JSON or CSV file
// @route   POST /api/patents/import
// @access  Private (Admin ideally, but using protect for now)
const importPatentFile = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded', errors: ['File is required'] });
    }

    const { path, mimetype } = req.file;

    const result = await importPatents(path, mimetype);

    // Clean up uploaded file
    if (fs.existsSync(path)) {
      fs.unlinkSync(path);
    }

    if (result.successCount === 0) {
      return res.status(400).json({ 
        success: false, 
        message: 'Failed to import any patents', 
        errors: result.errors 
      });
    }

    res.status(201).json({
      success: true,
      message: `Successfully imported ${result.successCount} patents (${result.failedCount} failed).`,
      data: result
    });

  } catch (error) {
    if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
    res.status(500).json({ success: false, message: 'Server error during import', errors: [error.message] });
  }
};

// @desc    Get all patents (paginated)
// @route   GET /api/patents
// @access  Private
const getPatents = async (req, res) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 10;
    const startIndex = (page - 1) * limit;

    const total = await Patent.countDocuments();
    const patents = await Patent.find().skip(startIndex).limit(limit).sort({ createdAt: -1 });

    res.status(200).json({
      success: true,
      message: 'Patents retrieved successfully',
      data: {
        total,
        page,
        limit,
        patents
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

// @desc    Get specific patent by ID
// @route   GET /api/patents/:id
// @access  Private
const getPatentById = async (req, res) => {
  try {
    const patent = await Patent.findById(req.params.id);

    if (!patent) {
      return res.status(404).json({ success: false, message: 'Patent not found', errors: [] });
    }

    // Also fetch chunks for debugging/verification
    const chunks = await PatentChunk.find({ patentId: patent._id }).sort({ chunkIndex: 1 });

    res.status(200).json({
      success: true,
      message: 'Patent retrieved successfully',
      data: {
        ...patent.toObject(),
        chunks
      }
    });
  } catch (error) {
    if (error.kind === 'ObjectId') {
      return res.status(400).json({ success: false, message: 'Invalid Patent ID format', errors: [] });
    }
    res.status(500).json({ success: false, message: 'Server error', errors: [error.message] });
  }
};

module.exports = {
  importPatentFile,
  getPatents,
  getPatentById
};
