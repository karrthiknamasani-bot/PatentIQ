const express = require('express');
const router = express.Router();
const { searchSimilar } = require('../controllers/searchController');

router.post('/similar', searchSimilar);

module.exports = router;
