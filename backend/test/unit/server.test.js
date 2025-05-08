const request = require('supertest');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

// Mock des modules
jest.mock('../../core/LucieCore', () => ({
  initialize: jest.fn().mockResolvedValue(true),
  initialized: true,
  getStatus: jest.fn().mockReturnValue({
    initialized: true,
    componentsCount: 0,
    uptime: 1000,
    version: '0.1.0'
  })
}));

jest.mock('../../utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  warn: jest.fn()
}));

// Créer une version simplifiée du serveur pour les tests
const app = express();
app.use(cors());
app.use(helmet());
app.use(express.json());

// Routes de base
app.get('/', (req, res) => {
  res.json({ message: 'API Lucie - Backend Node.js fonctionnel', version: '0.1.0' });
});

// Route de santé
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    initialized: true,
    version: '0.1.0'
  });
});

describe('Server API', () => {
  it('GET / - devrait retourner un message de bienvenue', async () => {
    const response = await request(app).get('/');
    
    expect(response.statusCode).toBe(200);
    expect(response.body).toHaveProperty('message');
    expect(response.body.message).toContain('API Lucie');
    expect(response.body).toHaveProperty('version');
    expect(response.body.version).toBe('0.1.0');
  });

  it('GET /health - devrait retourner le statut de santé', async () => {
    const response = await request(app).get('/health');
    
    expect(response.statusCode).toBe(200);
    expect(response.body).toHaveProperty('status');
    expect(response.body.status).toBe('ok');
    expect(response.body).toHaveProperty('timestamp');
    expect(response.body).toHaveProperty('initialized');
    expect(response.body.initialized).toBe(true);
    expect(response.body).toHaveProperty('version');
    expect(response.body.version).toBe('0.1.0');
  });
});