require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
// Temporarily commenting out LucieCore to isolate the issue
// const lucieCore = require('./core/LucieCore');
const logger = require('./utils/logger');

// Verify required environment variables
const requiredEnvVars = [
  'NODE_ENV',
  'PORT',
  'PYTHON_API_URL',
  'GRPC_SERVER',
  'NEO4J_URI',
  'NEO4J_USER',
  'NEO4J_PASSWORD',
  'REDIS_URL'
];

const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);
if (missingEnvVars.length > 0) {
  logger.warn(`Missing environment variables: ${missingEnvVars.join(', ')}`);
  logger.info('Please check your .env file or environment settings');
}

// Routes API
// Temporarily commenting out chat routes
// const chatRoutes = require('./api/routes/chatRoutes');

// Initialize Express application
const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());

// Basic error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', { error: error.message, stack: error.stack });
  // Keep the process running, but log the error
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection:', { reason: reason, promise: promise });
  // Keep the process running, but log the error
});

// Start the server
const server = app.listen(PORT, '0.0.0.0', () => {
  logger.info(`Lucie server started on port ${PORT}`);
  console.log(`Lucie server started on port ${PORT}`);
  
  // Temporarily commenting out Lucie Core initialization
  // Just log a message for now
  console.log('Skipping LucieCore initialization for debugging');
  logger.info('Skipping LucieCore initialization for debugging');
}).on('error', (err) => {
  logger.error(`Failed to start server: ${err.message}`);
  // Don't exit the process to prevent container restarts
  console.error(`Failed to start server: ${err.message}`);
});

// Base routes
app.get('/', (req, res) => {
  res.json({ 
    message: 'Lucie API - Node.js backend operational (LIMITED FUNCTIONALITY - DEBUG MODE)', 
    version: '0.1.0',
    debug: true
  });
});

// Health route
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    initialized: false, // Since we're not loading LucieCore
    version: '0.1.0',
    debug: true
  });
});

// API routes - Temporarily disabled
// app.use('/api/chat', chatRoutes);

// Temporary debug route to test if server is responding
app.get('/debug', (req, res) => {
  res.json({
    message: 'Debug endpoint is working',
    timestamp: new Date().toISOString()
  });
});

// Global error handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error', { 
    error: err.message,
    stack: err.stack,
    path: req.path 
  });
  res.status(500).json({ error: 'An error occurred on the server' });
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});