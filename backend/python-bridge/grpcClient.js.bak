/**
 * Client gRPC pour la communication avec le backend Python
 * Fournit des méthodes hautes performances pour échanger avec les services Python
 */

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");
const logger = require("../utils/logger");
const config = require("../utils/config");
const axios = require("axios");

class PythonBridge {
  constructor() {
    this.grpcClient = null;
    this.connected = false;
    this.fallbackToRest = false;
    this.services = new Map();

    // Configuration
    this.config = {
      grpcServer: config.pythonApi?.grpcServer || "lucie-python:50051",
      restApiUrl: config.pythonApi?.url || "http://lucie-python:8000",
      timeout: config.pythonApi?.timeout || 30000,
      protoPath: path.join(
        __dirname,
        "../../shared/communication/grpc/protos/lucie_service.proto"
      ),
    };

    logger.info("PythonBridge: Instance créée", {
      grpcServer: this.config.grpcServer,
      restApiUrl: this.config.restApiUrl,
    });
  }

  /**
   * Initialise la connexion gRPC avec le backend Python
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("PythonBridge: Initialisation de la connexion gRPC...");

      // Vérifier d'abord si le service REST est disponible (plus simple)
      try {
        const healthResponse = await axios.get(
          `${this.config.restApiUrl}/health`,
          {
            timeout: 5000,
          }
        );

        if (healthResponse.status === 200) {
          logger.info("PythonBridge: API REST Python disponible");
        } else {
          logger.warn(
            "PythonBridge: API REST Python répond mais avec un statut non-OK",
            {
              status: healthResponse.status,
            }
          );
        }
      } catch (restError) {
        logger.error("PythonBridge: API REST Python non disponible", {
          error: restError.message,
        });
        // Pour le moment, on continue. Le service gRPC peut être disponible séparément.
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
          }
        );

        // Vérifier la connexion gRPC
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
        logger.info("PythonBridge: Connexion gRPC établie");

        // Récupérer les services disponibles
        await this.discoverServices();

        return true;
      } catch (grpcError) {
        logger.error("PythonBridge: Échec de la connexion gRPC", {
          error: grpcError.message,
          stack: grpcError.stack,
        });

        this.fallbackToRest = true;
        logger.warn("PythonBridge: Passage en mode REST (fallback)");

        // Même en cas d'échec, on découvre tout de même les services via REST
        await this.discoverServicesRest();

        return this.services.size > 0;
      }
    } catch (error) {
      logger.error("PythonBridge: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      return false;
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
              "PythonBridge: Erreur lors de la découverte des services",
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

          logger.info("PythonBridge: Services découverts", {
            count: this.services.size,
            services: Array.from(this.services.keys()),
          });

          resolve(this.services);
        });
      });
    } catch (error) {
      logger.error("PythonBridge: Erreur lors de la découverte des services", {
        error: error.message,
      });
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

        logger.info("PythonBridge: Services découverts via REST", {
          count: this.services.size,
          services: Array.from(this.services.keys()),
        });
      }

      return this.services;
    } catch (error) {
      logger.error(
        "PythonBridge: Erreur lors de la découverte des services via REST",
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
                  `PythonBridge: Erreur lors de la vérification du service ${serviceName}`,
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
        `PythonBridge: Erreur lors de la vérification du service ${serviceName}`,
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

      logger.debug(`PythonBridge: Appel de ${serviceName}.${methodName}`, {
        dataSize: JSON.stringify(data).length,
      });

      // Appeler la méthode
      if (this.fallbackToRest) {
        // Utiliser REST
        const response = await axios.post(
          `${this.config.restApiUrl}/services/${serviceName}/${methodName}`,
          data,
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
                  `PythonBridge: Erreur lors de l'appel de ${serviceName}.${methodName}`,
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
                  `PythonBridge: Erreur lors du parsing du résultat de ${serviceName}.${methodName}`,
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
        `PythonBridge: Erreur lors de l'appel de ${serviceName}.${methodName}`,
        {
          error: error.message,
          stack: error.stack,
        }
      );
      throw error;
    }
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

      logger.debug("PythonBridge: Traitement de message", {
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
                  "PythonBridge: Erreur lors du traitement du message",
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
      logger.error("PythonBridge: Erreur lors du traitement du message", {
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }
}

module.exports = PythonBridge;
