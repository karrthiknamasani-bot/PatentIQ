const embeddingService = require('../services/embeddingService');

// @desc    Test Semantic Search Query against ChromaDB
// @route   POST /api/search/similar
// @access  Public or Protected
const searchSimilar = async (req, res) => {
  try {
    const { query, topK } = req.body;

    if (!query) {
      return res.status(400).json({ success: false, message: 'Query string is required' });
    }

    const limit = parseInt(topK, 10) || 5;

    // Call the embedding service to strictly perform vector matching
    const results = await embeddingService.searchSimilar(query, limit);

    res.status(200).json({
      success: true,
      message: 'Semantic search completed',
      data: results
    });

  } catch (error) {
    res.status(500).json({ success: false, message: 'Search failed', error: error.message });
  }
};

module.exports = {
  searchSimilar
};
