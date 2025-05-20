/**
 * Système d'intégration des agents Lucie
 * Module principal pour la gestion et la coordination des agents-ouvriers
 */

class LucieAgentSystem {
  /**
   * Initialise le système d'agents
   * @param {Object} config - Configuration du système d'agents
   */
  constructor(config = {}) {
    this.agents = new Map();
    this.chantiers = new Map();
    this.managerAgents = new Map();
    this.config = {
      maxAgentsPerChantier: config.maxAgentsPerChantier || 5,
      autoDiscoverAgents: config.autoDiscoverAgents !== false,
      enableValidation: config.enableValidation !== false,
      logLevel: config.logLevel || "info",
      ...config,
    };

    this.communicationBus = new EventEmitter();
    this.registry = new AgentRegistry(this.communicationBus);
    this.router = new AgentRouter(this.registry, this.communicationBus);
    this.organizer = new AgentOrganizer(this.registry, this.communicationBus);

    this.initialized = false;
    this.logger = new Logger(this.config.logLevel, "LucieAgentSystem");

    this.logger.info("Système d'agents Lucie créé");
  }

  /**
   * Initialise le système d'agents
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      this.logger.info("Initialisation du système d'agents Lucie...");

      // Initialiser le registre d'agents
      await this.registry.initialize();

      // Découvrir automatiquement les agents disponibles
      if (this.config.autoDiscoverAgents) {
        await this.discoverAgents();
      }

      // Organiser les agents en chantiers
      await this.organizer.organizeChantiers();

      this.initialized = true;
      this.logger.info("Système d'agents Lucie initialisé avec succès");

      return true;
    } catch (error) {
      this.logger.error(
        "Erreur lors de l'initialisation du système d'agents",
        error
      );
      return false;
    }
  }

  /**
   * Découvre automatiquement les agents disponibles
   * @returns {Promise<Array>} Liste des agents découverts
   */
  async discoverAgents() {
    try {
      this.logger.info("Découverte automatique des agents...");

      // Liste des dossiers à scanner pour les agents
      const agentDirectories = [
        "./agents/cybersecurity",
        "./agents/web-intelligence",
        "./agents/data",
        "./agents/managers",
      ];

      let discoveredAgents = [];

      for (const directory of agentDirectories) {
        const agents = await this.registry.discoverAgentsInDirectory(directory);
        discoveredAgents = [...discoveredAgents, ...agents];
      }

      this.logger.info(`${discoveredAgents.length} agents découverts`);

      return discoveredAgents;
    } catch (error) {
      this.logger.error("Erreur lors de la découverte des agents", error);
      return [];
    }
  }

  /**
   * Vérifie si le système est initialisé
   * @returns {Promise<boolean>} État d'initialisation
   */
  async ensureInitialized() {
    if (this.initialized) {
      return true;
    }

    return await this.initialize();
  }

  /**
   * Traite une requête avec les agents appropriés
   * @param {Object} request - Requête à traiter
   * @returns {Promise<Object>} Résultat du traitement
   */
  async processRequest(request) {
    await this.ensureInitialized();

    this.logger.debug("Traitement de requête", { requestType: request.type });

    // Router la requête vers les agents appropriés
    const result = await this.router.routeRequest(request);

    return result;
  }

  /**
   * Enregistre un nouvel agent
   * @param {Object} agent - Agent à enregistrer
   * @returns {Promise<Object>} Agent enregistré
   */
  async registerAgent(agent) {
    await this.ensureInitialized();

    this.logger.info(`Enregistrement de l'agent: ${agent.name}`);

    // Vérifier si l'agent implémente l'interface requise
    if (!agent.process || !agent.can_handle) {
      throw new Error(
        "L'agent doit implémenter les méthodes process() et can_handle()"
      );
    }

    // Enregistrer l'agent dans le registre
    const registeredAgent = await this.registry.registerAgent(agent);

    // Réorganiser les chantiers si nécessaire
    await this.organizer.reorganizeChantiers();

    return registeredAgent;
  }

  /**
   * Récupère la liste des agents disponibles
   * @param {string} type - Type d'agent (optionnel)
   * @returns {Promise<Array>} Liste des agents
   */
  async getAgents(type) {
    await this.ensureInitialized();

    if (type) {
      return await this.registry.getAgentsByType(type);
    }

    return await this.registry.getAllAgents();
  }

  /**
   * Récupère la liste des chantiers
   * @returns {Promise<Array>} Liste des chantiers
   */
  async getChantiers() {
    await this.ensureInitialized();

    return await this.organizer.getChantiers();
  }

  /**
   * Récupère les statistiques du système d'agents
   * @returns {Promise<Object>} Statistiques du système
   */
  async getStats() {
    await this.ensureInitialized();

    const registryStats = await this.registry.getStats();
    const routerStats = await this.router.getStats();
    const organizerStats = await this.organizer.getStats();

    return {
      agents: {
        total: registryStats.totalAgents,
        byType: registryStats.agentsByType,
        byCategory: registryStats.agentsByCategory,
      },
      chantiers: {
        total: organizerStats.totalChantiers,
        details: organizerStats.chantierDetails,
      },
      requests: {
        total: routerStats.totalRequests,
        successful: routerStats.successfulRequests,
        failed: routerStats.failedRequests,
        averageProcessingTime: routerStats.averageProcessingTime,
      },
      system: {
        initialized: this.initialized,
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
      },
    };
  }
}

/**
 * Registre des agents
 * Gère l'enregistrement et la récupération des agents
 */
class AgentRegistry {
  /**
   * Initialise le registre d'agents
   * @param {EventEmitter} eventBus - Bus d'événements pour la communication
   */
  constructor(eventBus) {
    this.agents = new Map();
    this.agentsByType = new Map();
    this.agentsByCategory = new Map();
    this.agentsByCapability = new Map();
    this.eventBus = eventBus;
    this.logger = new Logger("info", "AgentRegistry");
  }

  /**
   * Initialise le registre
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    this.logger.info("Initialisation du registre d'agents");
    return true;
  }

  /**
   * Enregistre un agent dans le registre
   * @param {Object} agent - Agent à enregistrer
   * @returns {Promise<Object>} Agent enregistré
   */
  async registerAgent(agent) {
    // Générer un ID si l'agent n'en a pas
    if (!agent.id) {
      agent.id = `agent_${Date.now()}_${Math.random()
        .toString(36)
        .substr(2, 9)}`;
    }

    // Enregistrer l'agent par ID
    this.agents.set(agent.id, agent);

    // Enregistrer par type
    if (!this.agentsByType.has(agent.agent_type)) {
      this.agentsByType.set(agent.agent_type, new Set());
    }
    this.agentsByType.get(agent.agent_type).add(agent.id);

    // Enregistrer par catégorie
    if (!this.agentsByCategory.has(agent.category)) {
      this.agentsByCategory.set(agent.category, new Set());
    }
    this.agentsByCategory.get(agent.category).add(agent.id);

    // Enregistrer par capacité
    if (agent.capabilities && Array.isArray(agent.capabilities)) {
      for (const capability of agent.capabilities) {
        if (!this.agentsByCapability.has(capability)) {
          this.agentsByCapability.set(capability, new Set());
        }
        this.agentsByCapability.get(capability).add(agent.id);
      }
    }

    // Émettre un événement d'enregistrement
    this.eventBus.emit("agent:registered", { agent });

    this.logger.info(`Agent enregistré: ${agent.name} (${agent.id})`);

    return agent;
  }

  /**
   * Supprime un agent du registre
   * @param {string} agentId - ID de l'agent à supprimer
   * @returns {Promise<boolean>} Succès de la suppression
   */
  async unregisterAgent(agentId) {
    const agent = this.agents.get(agentId);

    if (!agent) {
      this.logger.warn(
        `Tentative de suppression d'un agent inexistant: ${agentId}`
      );
      return false;
    }

    // Supprimer des collections
    this.agents.delete(agentId);

    if (this.agentsByType.has(agent.agent_type)) {
      this.agentsByType.get(agent.agent_type).delete(agentId);
    }

    if (this.agentsByCategory.has(agent.category)) {
      this.agentsByCategory.get(agent.category).delete(agentId);
    }

    if (agent.capabilities && Array.isArray(agent.capabilities)) {
      for (const capability of agent.capabilities) {
        if (this.agentsByCapability.has(capability)) {
          this.agentsByCapability.get(capability).delete(agentId);
        }
      }
    }

    // Émettre un événement de suppression
    this.eventBus.emit("agent:unregistered", { agentId, agent });

    this.logger.info(`Agent supprimé: ${agent.name} (${agentId})`);

    return true;
  }

  /**
   * Récupère un agent par son ID
   * @param {string} agentId - ID de l'agent
   * @returns {Promise<Object>} Agent trouvé
   */
  async getAgent(agentId) {
    return this.agents.get(agentId);
  }

  /**
   * Récupère tous les agents
   * @returns {Promise<Array>} Liste des agents
   */
  async getAllAgents() {
    return Array.from(this.agents.values());
  }

  /**
   * Récupère les agents par type
   * @param {string} type - Type d'agent
   * @returns {Promise<Array>} Liste des agents
   */
  async getAgentsByType(type) {
    if (!this.agentsByType.has(type)) {
      return [];
    }

    const agentIds = Array.from(this.agentsByType.get(type));
    return agentIds.map((id) => this.agents.get(id)).filter(Boolean);
  }

  /**
   * Récupère les agents par catégorie
   * @param {string} category - Catégorie d'agent
   * @returns {Promise<Array>} Liste des agents
   */
  async getAgentsByCategory(category) {
    if (!this.agentsByCategory.has(category)) {
      return [];
    }

    const agentIds = Array.from(this.agentsByCategory.get(category));
    return agentIds.map((id) => this.agents.get(id)).filter(Boolean);
  }

  /**
   * Récupère les agents par capacité
   * @param {string} capability - Capacité requise
   * @returns {Promise<Array>} Liste des agents
   */
  async getAgentsByCapability(capability) {
    if (!this.agentsByCapability.has(capability)) {
      return [];
    }

    const agentIds = Array.from(this.agentsByCapability.get(capability));
    return agentIds.map((id) => this.agents.get(id)).filter(Boolean);
  }

  /**
   * Découvre les agents dans un répertoire
   * @param {string} directory - Répertoire à scanner
   * @returns {Promise<Array>} Agents découverts
   */
  async discoverAgentsInDirectory(directory) {
    // Cette méthode serait plus complexe dans une implémentation réelle
    // avec lecture de fichiers, importation dynamique, etc.
    this.logger.info(`Scan du répertoire pour agents: ${directory}`);

    // Pour l'exemple, on simule la découverte d'agents
    const simulatedAgents = [];

    if (directory.includes("cybersecurity")) {
      simulatedAgents.push({
        id: `nmap_${Date.now()}`,
        name: "Nmap Scanner",
        description: "Agent d'analyse de réseau avec Nmap",
        capabilities: [
          "network_scanning",
          "port_discovery",
          "service_detection",
        ],
        agent_type: "specialized",
        category: "cybersecurity",
        process: async (input) => ({ result: "Nmap scan results" }),
        can_handle: (request) => request.type === "network_scan",
      });
    }

    if (directory.includes("data")) {
      simulatedAgents.push({
        id: `data_viz_${Date.now()}`,
        name: "Data Visualizer",
        description: "Agent de visualisation de données",
        capabilities: ["data_visualization", "chart_generation"],
        agent_type: "specialized",
        category: "data",
        process: async (input) => ({ result: "Data visualization generated" }),
        can_handle: (request) => request.type === "data_visualization",
      });
    }

    // Enregistrer les agents découverts
    for (const agent of simulatedAgents) {
      await this.registerAgent(agent);
    }

    return simulatedAgents;
  }

  /**
   * Récupère les statistiques du registre
   * @returns {Promise<Object>} Statistiques
   */
  async getStats() {
    const agentsByType = {};
    for (const [type, agents] of this.agentsByType.entries()) {
      agentsByType[type] = agents.size;
    }

    const agentsByCategory = {};
    for (const [category, agents] of this.agentsByCategory.entries()) {
      agentsByCategory[category] = agents.size;
    }

    return {
      totalAgents: this.agents.size,
      agentsByType,
      agentsByCategory,
    };
  }
}

/**
 * Routeur d'agents
 * Détermine l'agent le plus approprié pour chaque requête
 */
class AgentRouter {
  /**
   * Initialise le routeur d'agents
   * @param {AgentRegistry} registry - Registre d'agents
   * @param {EventEmitter} eventBus - Bus d'événements
   */
  constructor(registry, eventBus) {
    this.registry = registry;
    this.eventBus = eventBus;
    this.logger = new Logger("info", "AgentRouter");
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageProcessingTime: 0,
    };
  }

  /**
   * Route une requête vers les agents appropriés
   * @param {Object} request - Requête à traiter
   * @returns {Promise<Object>} Résultat du traitement
   */
  async routeRequest(request) {
    const startTime = Date.now();
    this.stats.totalRequests++;

    try {
      this.logger.debug("Routage de requête", { type: request.type });

      // Trouver le meilleur agent pour cette requête
      const agent = await this._findBestAgent(request);

      if (!agent) {
        this.logger.warn("Aucun agent capable de traiter cette requête", {
          type: request.type,
        });
        this.stats.failedRequests++;

        return {
          success: false,
          error: "Aucun agent capable de traiter cette requête",
          requestType: request.type,
        };
      }

      // Traiter la requête avec l'agent
      this.logger.info(`Traitement de la requête avec l'agent: ${agent.name}`);
      const result = await agent.process(request);

      // Valider le résultat avec des agents managers
      const validationResult = await this._validateResult(result, agent);

      // Mise à jour des statistiques
      this.stats.successfulRequests++;
      const processingTime = Date.now() - startTime;
      this.stats.averageProcessingTime =
        (this.stats.averageProcessingTime *
          (this.stats.successfulRequests - 1) +
          processingTime) /
        this.stats.successfulRequests;

      // Retourner le résultat
      return {
        success: true,
        result,
        validation: validationResult,
        agent: {
          id: agent.id,
          name: agent.name,
          type: agent.agent_type,
        },
        processingTime,
      };
    } catch (error) {
      this.logger.error("Erreur lors du routage de la requête", error);
      this.stats.failedRequests++;

      return {
        success: false,
        error: error.message,
        requestType: request.type,
      };
    }
  }

  /**
   * Trouve le meilleur agent pour une requête
   * @param {Object} request - Requête à traiter
   * @returns {Promise<Object>} Meilleur agent
   * @private
   */
  async _findBestAgent(request) {
    // Récupérer tous les agents
    const allAgents = await this.registry.getAllAgents();

    // Filtrer les agents capables de traiter la requête
    const capableAgents = [];

    for (const agent of allAgents) {
      try {
        if (agent.can_handle && agent.can_handle(request)) {
          capableAgents.push(agent);
        }
      } catch (error) {
        this.logger.warn(
          `Erreur lors de la vérification de la capacité de l'agent ${agent.name}`,
          error
        );
      }
    }

    if (capableAgents.length === 0) {
      return null;
    }

    // Trier les agents par pertinence pour la requête
    // Dans une implémentation réelle, on utiliserait un algorithme plus sophistiqué
    // qui prendrait en compte l'historique, la charge, etc.
    const sortedAgents = capableAgents.sort((a, b) => {
      // Préférer les agents spécialisés aux agents génériques
      if (a.agent_type === "specialized" && b.agent_type !== "specialized")
        return -1;
      if (a.agent_type !== "specialized" && b.agent_type === "specialized")
        return 1;

      // Priorité basée sur les capacités
      const aMatchScore = this._calculateMatchScore(a, request);
      const bMatchScore = this._calculateMatchScore(b, request);

      return bMatchScore - aMatchScore;
    });

    return sortedAgents[0];
  }

  /**
   * Calcule un score de correspondance entre un agent et une requête
   * @param {Object} agent - Agent à évaluer
   * @param {Object} request - Requête à traiter
   * @returns {number} Score de correspondance
   * @private
   */
  _calculateMatchScore(agent, request) {
    let score = 0;

    // Score de base pour la capacité à traiter la requête
    score += 10;

    // Bonus pour les capacités spécifiques
    if (agent.capabilities && Array.isArray(agent.capabilities)) {
      if (request.type && agent.capabilities.includes(request.type)) {
        score += 5;
      }

      // Bonus pour chaque capacité pertinente
      for (const capability of agent.capabilities) {
        if (request.capabilities && request.capabilities.includes(capability)) {
          score += 2;
        }
      }
    }

    // Bonus pour les agents de la même catégorie que la requête
    if (request.category && agent.category === request.category) {
      score += 3;
    }

    return score;
  }

  /**
   * Valide un résultat avec des agents managers
   * @param {Object} result - Résultat à valider
   * @param {Object} primaryAgent - Agent qui a produit le résultat
   * @returns {Promise<Object>} Résultat de la validation
   * @private
   */
  async _validateResult(result, primaryAgent) {
    // Récupérer les agents managers
    const managerAgents = await this.registry.getAgentsByType("manager");

    if (managerAgents.length === 0) {
      return { validated: true, score: 1.0, validations: [] };
    }

    const validations = [];
    let totalScore = 0;

    // Faire valider le résultat par chaque agent manager
    for (const manager of managerAgents) {
      try {
        // Créer une requête de validation
        const validationRequest = {
          type: "validation",
          content: {
            result,
            agent: {
              id: primaryAgent.id,
              name: primaryAgent.name,
              type: primaryAgent.agent_type,
            },
          },
        };

        // Vérifier si l'agent manager peut traiter cette validation
        if (manager.can_handle(validationRequest)) {
          const validation = await manager.process(validationRequest);

          validations.push({
            managerId: manager.id,
            managerName: manager.name,
            score: validation.score || 0,
            issues: validation.issues || [],
            suggestions: validation.suggestions || [],
          });

          totalScore += validation.score || 0;
        }
      } catch (error) {
        this.logger.warn(
          `Erreur lors de la validation par l'agent ${manager.name}`,
          error
        );
        validations.push({
          managerId: manager.id,
          managerName: manager.name,
          error: error.message,
          score: 0,
        });
      }
    }

    // Calculer le score moyen
    const averageScore =
      validations.length > 0 ? totalScore / validations.length : 1.0;

    return {
      validated: averageScore >= 0.7, // Seuil de validation
      score: averageScore,
      validations,
    };
  }

  /**
   * Récupère les statistiques du routeur
   * @returns {Promise<Object>} Statistiques
   */
  async getStats() {
    return this.stats;
  }
}

/**
 * Organisateur de chantiers
 * Regroupe les agents en chantiers spécialisés
 */
class AgentOrganizer {
  /**
   * Initialise l'organisateur de chantiers
   * @param {AgentRegistry} registry - Registre d'agents
   * @param {EventEmitter} eventBus - Bus d'événements
   */
  constructor(registry, eventBus) {
    this.registry = registry;
    this.eventBus = eventBus;
    this.chantiers = new Map();
    this.logger = new Logger("info", "AgentOrganizer");
  }

  /**
   * Organise les agents en chantiers
   * @returns {Promise<Object>} Chantiers organisés
   */
  async organizeChantiers() {
    this.logger.info("Organisation des agents en chantiers");

    // Réinitialiser les chantiers
    this.chantiers.clear();

    // Récupérer tous les agents
    const allAgents = await this.registry.getAllAgents();

    // Créer des chantiers par catégorie
    const categorizedAgents = new Map();

    for (const agent of allAgents) {
      const category = agent.category || "general";

      if (!categorizedAgents.has(category)) {
        categorizedAgents.set(category, []);
      }

      categorizedAgents.get(category).push(agent);
    }

    // Créer les chantiers
    for (const [category, agents] of categorizedAgents.entries()) {
      const chantierId = `chantier_${category}`;

      this.chantiers.set(chantierId, {
        id: chantierId,
        name: `Chantier ${
          category.charAt(0).toUpperCase() + category.slice(1)
        }`,
        category,
        agents: agents.map((a) => a.id),
        createdAt: new Date().toISOString(),
      });

      this.logger.info(
        `Chantier créé: ${chantierId} avec ${agents.length} agents`
      );
    }

    // Émettre un événement de réorganisation
    this.eventBus.emit("chantiers:organized", {
      chantiers: Array.from(this.chantiers.values()),
    });

    return this.chantiers;
  }

  /**
   * Réorganise les chantiers si nécessaire
   * @returns {Promise<boolean>} Succès de la réorganisation
   */
  async reorganizeChantiers() {
    this.logger.info("Réorganisation des chantiers");

    // Pour simplifier, on relance une organisation complète
    await this.organizeChantiers();

    return true;
  }

  /**
   * Récupère la liste des chantiers
   * @returns {Promise<Array>} Liste des chantiers
   */
  async getChantiers() {
    return Array.from(this.chantiers.values());
  }

  /**
   * Récupère un chantier par son ID
   * @param {string} chantierId - ID du chantier
   * @returns {Promise<Object>} Chantier trouvé
   */
  async getChantier(chantierId) {
    return this.chantiers.get(chantierId);
  }

  /**
   * Récupère les agents d'un chantier
   * @param {string} chantierId - ID du chantier
   * @returns {Promise<Array>} Liste des agents
   */
  async getChantierAgents(chantierId) {
    const chantier = await this.getChantier(chantierId);

    if (!chantier) {
      return [];
    }

    const agents = [];

    for (const agentId of chantier.agents) {
      const agent = await this.registry.getAgent(agentId);
      if (agent) {
        agents.push(agent);
      }
    }

    return agents;
  }

  /**
   * Récupère les statistiques de l'organisateur
   * @returns {Promise<Object>} Statistiques
   */
  async getStats() {
    const chantierDetails = {};

    for (const [chantierId, chantier] of this.chantiers.entries()) {
      chantierDetails[chantierId] = {
        name: chantier.name,
        category: chantier.category,
        agentCount: chantier.agents.length,
      };
    }

    return {
      totalChantiers: this.chantiers.size,
      chantierDetails,
    };
  }
}

/**
 * Logger simplifié pour le système d'agents
 */
class Logger {
  /**
   * Initialise le logger
   * @param {string} level - Niveau de log
   * @param {string} namespace - Espace de noms
   */
  constructor(level = "info", namespace = "LucieAgent") {
    this.level = level;
    this.namespace = namespace;
    this.levels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
    };
  }

  /**
   * Détermine si un niveau de log doit être affiché
   * @param {string} level - Niveau de log
   * @returns {boolean} Vrai si le niveau doit être affiché
   */
  shouldLog(level) {
    return this.levels[level] >= this.levels[this.level];
  }

  /**
   * Écrit un message de log
   * @param {string} level - Niveau de log
   * @param {string} message - Message à logger
   * @param {Object} meta - Métadonnées supplémentaires
   */
  log(level, message, meta = {}) {
    if (!this.shouldLog(level)) {
      return;
    }

    const timestamp = new Date().toISOString();
    const metaString = Object.keys(meta).length > 0 ? JSON.stringify(meta) : "";

    console.log(
      `[${timestamp}] [${
        this.namespace
      }] [${level.toUpperCase()}] ${message} ${metaString}`
    );
  }

  /**
   * Log de niveau debug
   * @param {string} message - Message à logger
   * @param {Object} meta - Métadonnées supplémentaires
   */
  debug(message, meta = {}) {
    this.log("debug", message, meta);
  }

  /**
   * Log de niveau info
   * @param {string} message - Message à logger
   * @param {Object} meta - Métadonnées supplémentaires
   */
  info(message, meta = {}) {
    this.log("info", message, meta);
  }

  /**
   * Log de niveau warn
   * @param {string} message - Message à logger
   * @param {Object} meta - Métadonnées supplémentaires
   */
  warn(message, meta = {}) {
    this.log("warn", message, meta);
  }

  /**
   * Log de niveau error
   * @param {string} message - Message à logger
   * @param {Object} meta - Métadonnées supplémentaires
   */
  error(message, meta = {}) {
    this.log("error", message, meta);
  }
}

/**
 * Simple EventEmitter pour la communication entre composants
 */
class EventEmitter {
  constructor() {
    this.events = {};
  }

  /**
   * Ajoute un écouteur d'événement
   * @param {string} event - Nom de l'événement
   * @param {Function} listener - Fonction à appeler lors de l'événement
   */
  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }

    this.events[event].push(listener);
  }

  /**
   * Émet un événement
   * @param {string} event - Nom de l'événement
   * @param {Object} data - Données associées à l'événement
   */
  emit(event, data) {
    if (!this.events[event]) {
      return;
    }

    this.events[event].forEach((listener) => {
      try {
        listener(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  /**
   * Supprime un écouteur d'événement
   * @param {string} event - Nom de l'événement
   * @param {Function} listener - Fonction à supprimer
   */
  off(event, listener) {
    if (!this.events[event]) {
      return;
    }

    this.events[event] = this.events[event].filter((l) => l !== listener);
  }
}

// Exportation des classes pour utilisation
module.exports = {
  LucieAgentSystem,
  AgentRegistry,
  AgentRouter,
  AgentOrganizer,
  Logger,
  EventEmitter,
};
