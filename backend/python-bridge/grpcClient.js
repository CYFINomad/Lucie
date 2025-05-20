/**
 * Bridge Python amélioré avec reconnexion automatique
 * Gère la communication avec le backend Python de manière plus robuste
 */

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");
const axios = require("axios");
const logger = require("../utils/logger");
const config = require("../utils/config");
const AsyncTaskManager = require("./asyncTasks");

class EnhancedPythonBridge {
  constructor() {
    this.grpcClient = null;
    this.connected = false;
    this.fallbackToRest = false;
    this.services = new Map();
    this.connectionRetries = 0;
    this.maxRetries = 5;
    this.retryInterval = 5000; // 5 secondes entre chaque tentative
    this.lastConnectionAttempt = 0;
    this.reconnectionTimeout = null;
    this.taskManager = AsyncTaskManager;

    // Configuration
    this.config = {
      grpcServer: config.pythonApi?.grpcServer || "lucie-python:50051",
      restApiUrl: config.pythonApi?.url || "http://lucie-python:8000",
      timeout: config.pythonApi?.timeout || 30000,
      protoPath: path.join(
        __dirname,
        "../../shared/communication/grpc/protos/lucie_service.proto"
      ),
      reconnectAutomatically: true,
      healthCheckInterval: 30000, // 30 secondes
    };

    logger.info("EnhancedPythonBridge: Instance créée", {
      grpcServer: this.config.grpcServer,
      restApiUrl: this.config.restApiUrl,
    });

    // Démarrer le healthcheck périodique
    if (this.config.reconnectAutomatically) {
      this.healthCheckInterval = setInterval(
        () => this.performHealthCheck(),
        this.config.healthCheckInterval
      );
    }
  }

  /**
   * Initialise la connexion avec le backend Python
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("EnhancedPythonBridge: Initialisation de la connexion...");

      // Éviter les tentatives trop fréquentes
      const now = Date.now();
      if (now - this.lastConnectionAttempt < this.retryInterval) {
        logger.warn(
          "EnhancedPythonBridge: Tentative de reconnexion trop rapide, attente..."
        );
        await new Promise((resolve) => setTimeout(resolve, this.retryInterval));
      }

      this.lastConnectionAttempt = Date.now();
      this.connectionRetries++;

      // Vérifier d'abord si le service REST est disponible
      try {
        const healthResponse = await axios.get(
          `${this.config.restApiUrl}/health`,
          {
            timeout: 5000,
          }
        );

        if (healthResponse.status === 200) {
          logger.info("EnhancedPythonBridge: API REST Python disponible");
        } else {
          logger.warn(
            "EnhancedPythonBridge: API REST Python répond mais avec un statut non-OK",
            {
              status: healthResponse.status,
            }
          );
        }
      } catch (restError) {
        logger.error("EnhancedPythonBridge: API REST Python non disponible", {
          error: restError.message,
        });

        // Si REST n'est pas disponible, essayer de programmer une reconnexion
        if (
          this.config.reconnectAutomatically &&
          this.connectionRetries < this.maxRetries
        ) {
          this._scheduleReconnection();
          return false;
        }

        // Si le nombre maximal de tentatives est atteint, abandonner
        if (this.connectionRetries >= this.maxRetries) {
          logger.error(
            `EnhancedPythonBridge: Nombre maximal de tentatives atteint (${this.maxRetries})`
          );
          return false;
        }
      }

      // Charger la définition du service depuis le fichier proto
      try {
        const packageDefinition = protoLoader.loadSync(this.config.protoPath, {
          keepCase: true,
          longs: String,
          enums: String,
          defaults: true,
          oneofs: true,
        });

        const protoDescriptor = grpc.loadPackageDefinition(packageDefinition);
        const lucieService = protoDescriptor.lucie.LucieService;

        // Créer le client gRPC
        this.grpcClient = new lucieService(
          this.config.grpcServer,
          grpc.credentials.createInsecure(), // En production, utiliser TLS
          {
            "grpc.max_receive_message_length": 1024 * 1024 * 100, // 100 MB
            "grpc.max_send_message_length": 1024 * 1024 * 100, // 100 MB
            "grpc.keepalive_time_ms": 10000, // Envoyer un ping toutes les 10 secondes
            "grpc.keepalive_timeout_ms": 5000, // Timeout de 5 secondes pour le ping
            "grpc.keepalive_permit_without_calls": 1, // Autoriser les pings même sans appels actifs
            "grpc.http2.min_time_between_pings_ms": 10000, // Temps minimum entre les pings
            "grpc.http2.max_pings_without_data": 0, // Nombre illimité de pings sans données
          }
        );

        // Vérifier la connexion gRPC
        try {
          const connectPromise = new Promise((resolve, reject) => {
            this.grpcClient.waitForReady(Date.now() + 5000, (error) => {
              if (error) {
                reject(error);
              } else {
                resolve(true);
              }
            });
          });

          await connectPromise;
          this.connected = true;
          this.fallbackToRest = false;
          logger.info("EnhancedPythonBridge: Connexion gRPC établie");

          // Réinitialiser le compteur de tentatives après une connexion réussie
          this.connectionRetries = 0;

          // Récupérer les services disponibles
          await this.discoverServices();

          return true;
        } catch (grpcConnectError) {
          logger.error("EnhancedPythonBridge: Échec de la connexion gRPC", {
            error: grpcConnectError.message,
          });

          // Fallback en mode REST
          this.fallbackToRest = true;
          logger.warn("EnhancedPythonBridge: Passage en mode REST (fallback)");

          // Même en cas d'échec, on découvre tout de même les services via REST
          await this.discoverServicesRest();

          return this.services.size > 0;
        }
      } catch (grpcSetupError) {
        logger.error(
          "EnhancedPythonBridge: Erreur lors de la configuration gRPC",
          {
            error: grpcSetupError.message,
            stack: grpcSetupError.stack,
          }
        );

        this.fallbackToRest = true;
        logger.warn("EnhancedPythonBridge: Passage en mode REST (fallback)");

        // Même en cas d'échec, on découvre tout de même les services via REST
        await this.discoverServicesRest();

        return this.services.size > 0;
      }
    } catch (error) {
      logger.error("EnhancedPythonBridge: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });

      // Programmer une reconnexion si nécessaire
      if (
        this.config.reconnectAutomatically &&
        this.connectionRetries < this.maxRetries
      ) {
        this._scheduleReconnection();
      }

      return false;
    }
  }

  /**
   * Programme une tentative de reconnexion
   * @private
   */
  _scheduleReconnection() {
    // Éviter les reconnexions multiples
    if (this.reconnectionTimeout) {
      clearTimeout(this.reconnectionTimeout);
    }

    // Calculer le délai avec backoff exponentiel
    const delay = Math.min(
      this.retryInterval * Math.pow(2, this.connectionRetries - 1),
      60000 // Maximum 1 minute entre les tentatives
    );

    logger.info(
      `EnhancedPythonBridge: Programmation d'une reconnexion dans ${delay}ms (tentative ${this.connectionRetries}/${this.maxRetries})`
    );

    this.reconnectionTimeout = setTimeout(async () => {
      logger.info("EnhancedPythonBridge: Tentative de reconnexion automatique");
      this.reconnectionTimeout = null;
      await this.initialize();
    }, delay);
  }

  /**
   * Effectue un healthcheck périodique
   * @private
   */
  async performHealthCheck() {
    // Si déjà connecté, vérifier que la connexion est toujours valide
    if (this.connected || this.fallbackToRest) {
      try {
        let healthOk = false;

        if (this.connected && !this.fallbackToRest) {
          // Vérifier la santé via gRPC
          try {
            await new Promise((resolve, reject) => {
              this.grpcClient.ping(
                {},
                { deadline: Date.now() + 3000 },
                (error, response) => {
                  if (error) {
                    reject(error);
                  } else {
                    resolve(response);
                  }
                }
              );
            });
            healthOk = true;
          } catch (grpcError) {
            logger.warn("EnhancedPythonBridge: Échec du healthcheck gRPC", {
              error: grpcError.message,
            });
            healthOk = false;
          }
        } else {
          // Vérifier la santé via REST
          try {
            const response = await axios.get(
              `${this.config.restApiUrl}/health`,
              {
                timeout: 3000,
              }
            );
            healthOk = response.status === 200;
          } catch (restError) {
            logger.warn("EnhancedPythonBridge: Échec du healthcheck REST", {
              error: restError.message,
            });
            healthOk = false;
          }
        }

        if (!healthOk) {
          logger.error(
            "EnhancedPythonBridge: Connexion perdue, tentative de reconnexion"
          );
          this.connected = false;
          this.connectionRetries = 0; // Réinitialiser pour une nouvelle série de tentatives
          await this.initialize();
        }
      } catch (error) {
        logger.error("EnhancedPythonBridge: Erreur lors du healthcheck", {
          error: error.message,
        });
      }
    }
    // Si non connecté, tenter une reconnexion
    else if (
      this.config.reconnectAutomatically &&
      this.connectionRetries < this.maxRetries
    ) {
      logger.info(
        "EnhancedPythonBridge: Non connecté, tentative de reconnexion"
      );
      await this.initialize();
    }
  }

  /**
   * Découvre les services disponibles via gRPC
   * @returns {Promise<Map>} Services disponibles
   */
  async discoverServices() {
    try {
      if (!this.connected || !this.grpcClient) {
        throw new Error("Client gRPC non connecté");
      }

      return new Promise((resolve, reject) => {
        this.grpcClient.listServices({}, (error, response) => {
          if (error) {
            logger.error(
              "EnhancedPythonBridge: Erreur lors de la découverte des services",
              {
                error: error.message,
              }
            );
            reject(error);
            return;
          }

          const services = response.services || [];

          for (const service of services) {
            this.services.set(service.name, {
              name: service.name,
              methods: service.methods || [],
              status: service.status || "available",
              metadata: service.metadata || {},
            });
          }

          logger.info("EnhancedPythonBridge: Services découverts", {
            count: this.services.size,
            services: Array.from(this.services.keys()),
          });

          resolve(this.services);
        });
      });
    } catch (error) {
      logger.error(
        "EnhancedPythonBridge: Erreur lors de la découverte des services",
        {
          error: error.message,
        }
      );
      return this.services;
    }
  }

  /**
   * Découvre les services disponibles via l'API REST (fallback)
   * @returns {Promise<Map>} Services disponibles
   */
  async discoverServicesRest() {
    try {
      const response = await axios.get(`${this.config.restApiUrl}/services`, {
        timeout: this.config.timeout,
      });

      if (response.status === 200 && response.data && response.data.services) {
        const services = response.data.services || [];

        for (const service of services) {
          this.services.set(service.name, {
            name: service.name,
            methods: service.methods || [],
            status: service.status || "available",
            metadata: service.metadata || {},
          });
        }

        logger.info("EnhancedPythonBridge: Services découverts via REST", {
          count: this.services.size,
          services: Array.from(this.services.keys()),
        });
      }

      return this.services;
    } catch (error) {
      logger.error(
        "EnhancedPythonBridge: Erreur lors de la découverte des services via REST",
        {
          error: error.message,
        }
      );
      return this.services;
    }
  }

  /**
   * Vérifie l'état d'un service
   * @param {string} serviceName - Nom du service à vérifier
   * @returns {Promise<Object>} État du service
   */
  async checkStatus(serviceName) {
    try {
      await this.ensureConnected();

      // Si le service n'est pas dans la liste, essayer de le découvrir
      if (!this.services.has(serviceName)) {
        if (this.fallbackToRest) {
          await this.discoverServicesRest();
        } else {
          await this.discoverServices();
        }
      }

      // Si toujours pas disponible, renvoyer un état non disponible
      if (!this.services.has(serviceName)) {
        return {
          available: false,
          name: serviceName,
          status: "not_found",
        };
      }

      // Vérifier l'état du service
      if (this.fallbackToRest) {
        // Utiliser REST pour vérifier l'état
        const response = await axios.get(
          `${this.config.restApiUrl}/services/${serviceName}/status`,
          {
            timeout: this.config.timeout,
          }
        );

        if (response.status === 200) {
          return {
            available: response.data.status === "available",
            name: serviceName,
            status: response.data.status,
            stats: response.data.stats || {},
          };
        } else {
          return {
            available: false,
            name: serviceName,
            status: "error",
            error: `Erreur HTTP ${response.status}`,
          };
        }
      } else {
        // Utiliser gRPC pour vérifier l'état
        return new Promise((resolve, reject) => {
          this.grpcClient.checkServiceStatus(
            { serviceName },
            (error, response) => {
              if (error) {
                logger.error(
                  `EnhancedPythonBridge: Erreur lors de la vérification du service ${serviceName}`,
                  {
                    error: error.message,
                  }
                );
                resolve({
                  available: false,
                  name: serviceName,
                  status: "error",
                  error: error.message,
                });
                return;
              }

              resolve({
                available: response.status === "available",
                name: serviceName,
                status: response.status,
                stats: response.stats || {},
              });
            }
          );
        });
      }
    } catch (error) {
      logger.error(
        `EnhancedPythonBridge: Erreur lors de la vérification du service ${serviceName}`,
        {
          error: error.message,
        }
      );

      return {
        available: false,
        name: serviceName,
        status: "error",
        error: error.message,
      };
    }
  }

  /**
   * S'assure que le bridge est connecté
   * @returns {Promise<boolean>} État de la connexion
   */
  async ensureConnected() {
    if (this.connected || this.fallbackToRest) {
      return true;
    }

    return this.initialize();
  }

  /**
   * Invoque une méthode sur un service Python
   * @param {string} serviceName - Nom du service
   * @param {string} methodName - Nom de la méthode
   * @param {Object} data - Données à envoyer
   * @returns {Promise<Object>} Résultat de l'appel
   */
  async invokeMethod(serviceName, methodName, data = {}) {
    try {
      await this.ensureConnected();

      // Vérifier que le service existe
      if (!this.services.has(serviceName)) {
        if (this.fallbackToRest) {
          await this.discoverServicesRest();
        } else {
          await this.discoverServices();
        }

        if (!this.services.has(serviceName)) {
          throw new Error(`Service "${serviceName}" non disponible`);
        }
      }

      // Vérifier que la méthode existe
      const service = this.services.get(serviceName);
      const methodExists = service.methods.some((m) => m.name === methodName);

      if (!methodExists) {
        throw new Error(
          `Méthode "${methodName}" non disponible sur le service "${serviceName}"`
        );
      }

      logger.debug(
        `EnhancedPythonBridge: Appel de ${serviceName}.${methodName}`,
        {
          dataSize: JSON.stringify(data).length,
        }
      );

      // Pour les méthodes longues, utiliser le gestionnaire de tâches asynchrones
      const isLongRunningMethod = this._isLongRunningMethod(
        serviceName,
        methodName
      );

      if (isLongRunningMethod) {
        return this._invokeAsyncMethod(serviceName, methodName, data);
      }

      // Appeler la méthode
      if (this.fallbackToRest) {
        // Utiliser REST
        const response = await axios.post(
          `${this.config.restApiUrl}/services/${serviceName}/${methodName}`,
          { data },
          {
            timeout: this.config.timeout,
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (response.status === 200) {
          return response.data.result || {};
        } else {
          throw new Error(
            `Erreur HTTP ${response.status} lors de l'appel de ${serviceName}.${methodName}`
          );
        }
      } else {
        // Utiliser gRPC
        return new Promise((resolve, reject) => {
          this.grpcClient.invokeMethod(
            {
              serviceName,
              methodName,
              data: JSON.stringify(data),
            },
            (error, response) => {
              if (error) {
                logger.error(
                  `EnhancedPythonBridge: Erreur lors de l'appel de ${serviceName}.${methodName}`,
                  {
                    error: error.message,
                  }
                );
                reject(error);
                return;
              }

              try {
                const result = JSON.parse(response.result);
                resolve(result);
              } catch (parseError) {
                logger.error(
                  `EnhancedPythonBridge: Erreur lors du parsing du résultat de ${serviceName}.${methodName}`,
                  {
                    error: parseError.message,
                  }
                );
                reject(parseError);
              }
            }
          );
        });
      }
    } catch (error) {
      logger.error(
        `EnhancedPythonBridge: Erreur lors de l'appel de ${serviceName}.${methodName}`,
        {
          error: error.message,
          stack: error.stack,
        }
      );
      throw error;
    }
  }

  /**
   * Vérifie si une méthode est considérée comme longue durée
   * @param {string} serviceName - Nom du service
   * @param {string} methodName - Nom de la méthode
   * @returns {boolean} Vrai si la méthode est longue durée
   * @private
   */
  _isLongRunningMethod(serviceName, methodName) {
    // Méthodes connues pour être longues durées
    const longRunningMethods = [
      { service: "learning", method: "learnFromUrl" },
      { service: "learning", method: "processLargeDocument" },
      { service: "multi_ai", method: "runExtensiveEvaluation" },
      { service: "knowledge", method: "buildCompleteGraph" },
    ];

    return longRunningMethods.some(
      (m) => m.service === serviceName && m.method === methodName
    );
  }

  /**
   * Invoque une méthode asynchrone et suit son progrès
   * @param {string} serviceName - Nom du service
   * @param {string} methodName - Nom de la méthode
   * @param {Object} data - Données à envoyer
   * @returns {Promise<Object>} Résultat de l'appel
   * @private
   */
  async _invokeAsyncMethod(serviceName, methodName, data) {
    logger.info(
      `EnhancedPythonBridge: Appel asynchrone de ${serviceName}.${methodName}`
    );

    // Créer une tâche asynchrone
    const taskId = await this.taskManager.createTask(
      `python_method_${serviceName}_${methodName}`,
      {
        serviceName,
        methodName,
        data,
      }
    );

    // Exécuter la tâche en arrière-plan
    this.taskManager.executeTask(
      `python_method_${serviceName}_${methodName}`,
      {
        serviceName,
        methodName,
        data,
      },
      async ({ taskId, params, updateProgress }) => {
        try {
          // Mettre à jour l'état de la tâche
          await updateProgress(10);

          // Appeler la méthode
          let result;
          if (this.fallbackToRest) {
            // Utiliser REST
            const response = await axios.post(
              `${this.config.restApiUrl}/services/${params.serviceName}/${params.methodName}`,
              { data: params.data },
              {
                timeout: this.config.timeout * 2, // Timeout plus long pour les méthodes asynchrones
                headers: {
                  "Content-Type": "application/json",
                },
              }
            );

            if (response.status === 200) {
              result = response.data.result || {};
            } else {
              throw new Error(
                `Erreur HTTP ${response.status} lors de l'appel asynchrone de ${params.serviceName}.${params.methodName}`
              );
            }
          } else {
            // Utiliser gRPC
            result = await new Promise((resolve, reject) => {
              this.grpcClient.invokeMethod(
                {
                  serviceName: params.serviceName,
                  methodName: params.methodName,
                  data: JSON.stringify(params.data),
                },
                (error, response) => {
                  if (error) {
                    reject(error);
                    return;
                  }

                  try {
                    const result = JSON.parse(response.result);
                    resolve(result);
                  } catch (parseError) {
                    reject(parseError);
                  }
                }
              );
            });
          }

          // Mettre à jour l'état de la tâche
          await updateProgress(100);

          return result;
        } catch (error) {
          logger.error(
            `EnhancedPythonBridge: Erreur lors de l'appel asynchrone de ${params.serviceName}.${params.methodName}`,
            {
              error: error.message,
              taskId,
            }
          );
          throw error;
        }
      }
    );

    return {
      taskId,
      status: "pending",
      async getResult(timeout = 60000) {
        return await this.taskManager.getTaskResult(taskId, { timeout });
      },
      async checkStatus() {
        const status = await this.taskManager.getTask(taskId);
        return status;
      },
      async cancel() {
        return await this.taskManager.cancelTask(taskId);
      },
    };
  }

  /**
   * Traite un message via le backend Python
   * @param {string} message - Message à traiter
   * @param {Object} context - Contexte de la conversation
   * @returns {Promise<Object>} Réponse traitée
   */
  async processMessage(message, context = {}) {
    try {
      await this.ensureConnected();

      logger.debug("EnhancedPythonBridge: Traitement de message", {
        messageLength: message.length,
      });

      if (this.fallbackToRest) {
        // Utiliser l'API REST pour le traitement du message
        const response = await axios.post(
          `${this.config.restApiUrl}/process-message`,
          {
            message,
            context,
          },
          {
            timeout: this.config.timeout,
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (response.status === 200) {
          return response.data;
        } else {
          throw new Error(
            `Erreur HTTP ${response.status} lors du traitement du message`
          );
        }
      } else {
        // Utiliser gRPC pour le traitement du message
        return new Promise((resolve, reject) => {
          this.grpcClient.processMessage(
            {
              message,
              context: JSON.stringify(context),
            },
            (error, response) => {
              if (error) {
                logger.error(
                  "EnhancedPythonBridge: Erreur lors du traitement du message",
                  {
                    error: error.message,
                  }
                );
                reject(error);
                return;
              }

              resolve({
                response: response.response,
                timestamp: response.timestamp,
                messageId: response.messageId,
                context: response.context ? JSON.parse(response.context) : {},
              });
            }
          );
        });
      }
    } catch (error) {
      logger.error(
        "EnhancedPythonBridge: Erreur lors du traitement du message",
        {
          error: error.message,
          stack: error.stack,
        }
      );
      throw error;
    }
  }

  /**
   * Ferme proprement les connexions
   */
  close() {
    logger.info("EnhancedPythonBridge: Fermeture des connexions");

    // Arrêter les vérifications périodiques
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }

    // Annuler toute tentative de reconnexion en cours
    if (this.reconnectionTimeout) {
      clearTimeout(this.reconnectionTimeout);
      this.reconnectionTimeout = null;
    }

    // Fermer la connexion gRPC
    if (this.grpcClient && this.connected) {
      this.grpcClient.close();
      this.grpcClient = null;
      this.connected = false;
    }

    logger.info("EnhancedPythonBridge: Connexions fermées");
  }
}

module.exports = EnhancedPythonBridge;
