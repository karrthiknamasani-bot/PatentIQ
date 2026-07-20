const express = require('express');
const router = express.Router();
const upload = require('../middleware/uploadMiddleware');
const { protect } = require('../middleware/authMiddleware');
const {
  uploadProject,
  getProjects,
  getProjectById,
  deleteProject
} = require('../controllers/projectController');

// Multer upload middleware parses the multipart form data.
// We expect a single file named 'document'
router.route('/upload').post(protect, upload.single('document'), uploadProject);

router.route('/')
  .get(protect, getProjects);

router.route('/:id')
  .get(protect, getProjectById)
  .delete(protect, deleteProject);

module.exports = router;
