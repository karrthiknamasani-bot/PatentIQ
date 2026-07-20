const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/authMiddleware');
const { processDocument, getProcessingStatus } = require('../controllers/processController');

router.post('/:projectId', protect, processDocument);
router.get('/:projectId/status', protect, getProcessingStatus);

module.exports = router;
