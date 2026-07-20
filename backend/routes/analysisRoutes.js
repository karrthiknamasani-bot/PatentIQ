const express = require('express');
const router = express.Router();
const { analyzeProject, getAnalysis } = require('../controllers/analysisController');
const { protect } = require('../middleware/authMiddleware');

router.post('/:projectId', protect, analyzeProject);
router.get('/:projectId', protect, getAnalysis);

module.exports = router;
