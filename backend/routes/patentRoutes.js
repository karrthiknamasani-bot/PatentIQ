const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const { protect } = require('../middleware/authMiddleware');
const { importPatentFile, getPatents, getPatentById } = require('../controllers/patentController');

// Ensure tmp upload dir exists for patent imports
const importDir = path.join(__dirname, '../uploads/imports');
if (!fs.existsSync(importDir)) {
  fs.mkdirSync(importDir, { recursive: true });
}

// Multer config for imports (JSON/CSV)
const storage = multer.diskStorage({
  destination(req, file, cb) {
    cb(null, importDir);
  },
  filename(req, file, cb) {
    cb(null, `import-${Date.now()}${path.extname(file.originalname)}`);
  },
});

const fileFilter = (req, file, cb) => {
  const allowedFileTypes = /csv|json/;
  const extname = allowedFileTypes.test(path.extname(file.originalname).toLowerCase());
  const mimetype = allowedFileTypes.test(file.mimetype) || file.mimetype === 'text/csv' || file.mimetype === 'application/json';

  if (extname && mimetype) {
    return cb(null, true);
  } else {
    cb(new Error('Unsupported file type. Only CSV and JSON are allowed for import.'));
  }
};

const uploadImport = multer({ 
  storage,
  fileFilter,
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB limit
});

router.post('/import', protect, uploadImport.single('file'), importPatentFile);
router.get('/', protect, getPatents);
router.get('/:id', protect, getPatentById);

module.exports = router;
