/**
 * Configuration centralisée pour le backend de Lucie
 * Charge les variables d'environnement et définit les valeurs par défaut
 */

// Conversion d'une chaîne en booléen
const toBool = (value) => {
    return value && value.toLowerCase() === 'true';
  };
  
  // Conversion d'une chaîne en nombre
  const toNumber = (value, defaultValue) => {
    const num = parseInt(value, 10);
    return isNaN(num) ? defaultValue : num;
  };
  
  const config = {
    // Environnement
    environment: process.env.NODE_ENV || 'development',
    isDevelopment: process.env.NODE_ENV !== 'production',
    
    // Serveur
    port: toNumber(process.env.PORT, 5000),
    
    // Communication avec Python
    pythonApi: {
      url: process.env.PYTHON_API_URL || 'http://lucie-python:8000',
      grpcServer: process.env.GRPC_SERVER || 'lucie-python:50051',
      timeout: toNumber(process.env.PYTHON_API_TIMEOUT, 30000)
    },
    
    // Base de données Neo4j
    neo4j: {
      uri: process.env.NEO4J_URI || 'bolt://neo4j:7687',
      user: process.env.NEO4J_USER || 'neo4j',
      password: process.env.NEO4J_PASSWORD || 'password',
      database: process.env.NEO4J_DATABASE || 'neo4j'
    },
    
    // Redis
    redis: {
      url: process.env.REDIS_URL || 'redis://redis:6379',
      prefix: process.env.REDIS_PREFIX || 'lucie:'
    },
    
    // Logging
    logging: {
      level: process.env.LOG_LEVEL || 'info',
      file: toBool(process.env.LOG_TO_FILE) || true
    },
    
    // Sécurité
    security: {
      jwtSecret: process.env.JWT_SECRET || 'your-secret-key-for-development-only',
      jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
      corsOrigins: (process.env.CORS_ORIGINS || '*').split(',')
    },
    
    // Fonctionnalités
    features: {
      multiAI: toBool(process.env.FEATURE_MULTI_AI) || false,
      voiceInput: toBool(process.env.FEATURE_VOICE_INPUT) || false,
      avatarVisual: toBool(process.env.FEATURE_AVATAR_VISUAL) || false,
      proactiveAssistance: toBool(process.env.FEATURE_PROACTIVE) || false
    }
  };
  
  module.exports = config;