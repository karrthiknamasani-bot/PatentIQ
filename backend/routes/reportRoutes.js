const express = require('express');
const router = express.Router();
const { generateReport, downloadReport, getProjectReports } = require('../controllers/reportController');
const { protect } = require('../middleware/authMiddleware');

// POST /api/report/:projectId
router.post('/:projectId', protect, generateReport);

// GET /api/report/project/:projectId
router.get('/project/:projectId', protect, getProjectReports);

// GET /api/report/:reportId
router.get('/:reportId', protect, downloadReport);

module.exports = router;
