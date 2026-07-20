const mongoose = require('mongoose');

const checkHealth = async (req, res) => {
  try {
    const dbState = mongoose.connection.readyState;
    const states = {
      0: 'disconnected',
      1: 'connected',
      2: 'connecting',
      3: 'disconnecting',
    };
    
    res.status(200).json({
      status: 'success',
      message: 'PatentIQ API is running',
      timestamp: new Date().toISOString(),
      database: states[dbState] || 'unknown',
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Health check failed',
      error: error.message,
    });
  }
};

module.exports = {
  checkHealth,
};
