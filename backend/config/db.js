const mongoose = require('mongoose');
const dns = require('dns');

const connectDB = async () => {
  try {
    console.log('Connecting to MongoDB...');
    dns.setServers(['8.8.8.8', '8.8.4.4']);
    const conn = await mongoose.connect(process.env.MONGO_URI);
    console.log(`MongoDB Connected Successfully: ${conn.connection.host}`);
  } catch (error) {
    console.error('MongoDB Connection Failed:');
    console.error(error); // Logs full stack trace
    process.exit(1);
  }
};

module.exports = connectDB;
