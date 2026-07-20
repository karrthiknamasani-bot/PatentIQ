const multer = require('multer');
const path = require('path');
const crypto = require('crypto');
const fs = require('fs');

// Ensure uploads directory exists
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Storage engine
const storage = multer.diskStorage({
  destination(req, file, cb) {
    cb(null, uploadDir);
  },
  filename(req, file, cb) {
    // Generate unique filename to prevent overwriting
    const uniqueSuffix = crypto.randomBytes(16).toString('hex');
    const ext = path.extname(file.originalname);
    cb(null, `${file.fieldname}-${uniqueSuffix}${ext}`);
  },
});

// File validation
const fileFilter = (req, file, cb) => {
  const allowedFileTypes = /pdf|docx|txt/;
  
  // Check extension
  const extname = allowedFileTypes.test(path.extname(file.originalname).toLowerCase());
  
  // Check mime
  const mimetype = allowedFileTypes.test(file.mimetype) || 
                   file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || 
                   file.mimetype === 'text/plain' || 
                   file.mimetype === 'application/pdf';

  if (extname && mimetype) {
    return cb(null, true);
  } else {
    cb(new Error('Unsupported file type. Only PDF, DOCX, and TXT are allowed.'));
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
});

module.exports = upload;
