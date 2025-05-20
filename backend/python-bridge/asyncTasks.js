/**
 * Gestionnaire de tâches asynchrones pour les opérations longues durées
 * Permet de suivre l'état des tâches et de récupérer les résultats
 */

const logger = require("../utils/logger");
const { v4: uuidv4 } = require("uuid");
const redis = require("ioredis");
const config = require("../utils/config");

class AsyncTaskManager {
  constructor() {
    this.tasks = new Map();
    this.redisClient = null;
    this.useRedis = config.redis && config.redis.url;
    this.redisKeyPrefix = config.redis?.prefix || "lucie:task:";
    this.initialized = false;

    // Auto-nettoyage des tâches terminées (10 minutes)
    this.cleanupInterval = setInterval(() => this.cleanupTasks(), 600000);

    logger.info("AsyncTaskManager: Instance créée");
  }

  /**
   * Initialise le gestionnaire de tâches
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("AsyncTaskManager: Initialisation...");

      if (this.useRedis) {
        try {
          this.redisClient = new redis(config.redis.url);

          // Tester la connexion Redis
          await this.redisClient.ping();
          logger.info("AsyncTaskManager: Connexion Redis établie");
        } catch (redisError) {
          logger.error("AsyncTaskManager: Erreur de connexion Redis", {
            error: redisError.message,
          });

          this.redisClient = null;
          this.useRedis = false;
        }
      }

      this.initialized = true;
      return true;
    } catch (error) {
      logger.error("AsyncTaskManager: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      return false;
    }
  }

  /**
   * S'assure que le gestionnaire est initialisé
   * @returns {Promise<boolean>} État de l'initialisation
   */
  async ensureInitialized() {
    if (this.initialized) {
      return true;
    }

    return this.initialize();
  }

  /**
   * Crée une nouvelle tâche
   * @param {string} type - Type de tâche
   * @param {Object} params - Paramètres de la tâche
   * @param {Object} options - Options de la tâche
   * @returns {Promise<string>} Identifiant de la tâche
   */
  async createTask(type, params = {}, options = {}) {
    await this.ensureInitialized();

    const taskId = uuidv4();
    const now = new Date();

    const task = {
      id: taskId,
      type,
      params,
      status: "pending",
      progress: 0,
      createdAt: now.toISOString(),
      updatedAt: now.toISOString(),
      timeout: options.timeout || 3600000, // 1 heure par défaut
      priority: options.priority || 5,
      tags: options.tags || [],
      owner: options.owner || "system",
      metadata: options.metadata || {},
    };

    // Stocker la tâche
    this.tasks.set(taskId, task);

    // Si Redis est disponible, stocker également dans Redis
    if (this.useRedis && this.redisClient) {
      try {
        const key = `${this.redisKeyPrefix}${taskId}`;
        await this.redisClient.set(key, JSON.stringify(task));

        // Définir un TTL pour éviter d'encombrer Redis
        await this.redisClient.expire(
          key,
          Math.ceil(task.timeout / 1000) + 86400
        ); // TTL + 1 jour
      } catch (redisError) {
        logger.error("AsyncTaskManager: Erreur lors du stockage Redis", {
          error: redisError.message,
          taskId,
        });
      }
    }

    logger.info("AsyncTaskManager: Tâche créée", {
      taskId,
      type,
      priority: task.priority,
    });

    return taskId;
  }

  /**
   * Met à jour l'état d'une tâche
   * @param {string} taskId - Identifiant de la tâche
   * @param {Object} updates - Mises à jour à appliquer
   * @returns {Promise<Object>} Tâche mise à jour
   */
  async updateTask(taskId, updates = {}) {
    await this.ensureInitialized();

    // Récupérer la tâche
    let task = await this.getTask(taskId);

    if (!task) {
      throw new Error(`Tâche "${taskId}" introuvable`);
    }

    // Appliquer les mises à jour
    const allowedUpdates = [
      "status",
      "progress",
      "result",
      "error",
      "metadata",
    ];
    const now = new Date();

    // Filtrer uniquement les mises à jour autorisées
    const filteredUpdates = Object.keys(updates)
      .filter((key) => allowedUpdates.includes(key))
      .reduce((obj, key) => {
        obj[key] = updates[key];
        return obj;
      }, {});

    // Mettre à jour la tâche
    task = {
      ...task,
      ...filteredUpdates,
      updatedAt: now.toISOString(),
    };

    // Si la tâche est terminée, enregistrer l'heure de fin
    if (updates.status === "completed" || updates.status === "failed") {
      task.completedAt = now.toISOString();
    }

    // Stocker la tâche mise à jour
    this.tasks.set(taskId, task);

    // Si Redis est disponible, mettre à jour dans Redis
    if (this.useRedis && this.redisClient) {
      try {
        const key = `${this.redisKeyPrefix}${taskId}`;
        await this.redisClient.set(key, JSON.stringify(task));
      } catch (redisError) {
        logger.error("AsyncTaskManager: Erreur lors de la mise à jour Redis", {
          error: redisError.message,
          taskId,
        });
      }
    }

    logger.debug("AsyncTaskManager: Tâche mise à jour", {
      taskId,
      status: task.status,
      progress: task.progress,
    });

    return task;
  }

  /**
   * Récupère l'état d'une tâche
   * @param {string} taskId - Identifiant de la tâche
   * @returns {Promise<Object>} État de la tâche
   */
  async getTask(taskId) {
    await this.ensureInitialized();

    // D'abord essayer de récupérer depuis la mémoire
    if (this.tasks.has(taskId)) {
      return this.tasks.get(taskId);
    }

    // Si Redis est disponible et que la tâche n'est pas en mémoire
    if (this.useRedis && this.redisClient) {
      try {
        const key = `${this.redisKeyPrefix}${taskId}`;
        const taskJson = await this.redisClient.get(key);

        if (taskJson) {
          const task = JSON.parse(taskJson);

          // Mise en cache en mémoire
          this.tasks.set(taskId, task);

          return task;
        }
      } catch (redisError) {
        logger.error("AsyncTaskManager: Erreur lors de la récupération Redis", {
          error: redisError.message,
          taskId,
        });
      }
    }

    return null;
  }

  /**
   * Exécute une fonction en tâche asynchrone
   * @param {string} type - Type de tâche
   * @param {Object} params - Paramètres de la tâche
   * @param {Function} executor - Fonction d'exécution (async)
   * @param {Object} options - Options de la tâche
   * @returns {Promise<string>} Identifiant de la tâche
   */
  async executeTask(type, params, executor, options = {}) {
    const taskId = await this.createTask(type, params, options);

    // Exécuter la tâche en arrière-plan
    setImmediate(async () => {
      try {
        // Marquer la tâche comme en cours
        await this.updateTask(taskId, { status: "running", progress: 0 });

        // Exécuter la fonction
        const result = await executor({
          taskId,
          params,
          updateProgress: async (progress) => {
            await this.updateTask(taskId, {
              progress: Math.max(0, Math.min(100, progress)),
            });
          },
        });

        // Marquer la tâche comme terminée
        await this.updateTask(taskId, {
          status: "completed",
          progress: 100,
          result,
        });

        logger.info("AsyncTaskManager: Tâche terminée avec succès", {
          taskId,
          type,
        });
      } catch (error) {
        // Marquer la tâche comme échouée
        await this.updateTask(taskId, {
          status: "failed",
          error: {
            message: error.message,
            stack: error.stack,
          },
        });

        logger.error(
          "AsyncTaskManager: Erreur lors de l'exécution de la tâche",
          {
            taskId,
            type,
            error: error.message,
            stack: error.stack,
          }
        );
      }
    });

    return taskId;
  }

  /**
   * Récupère le résultat d'une tâche (attend si nécessaire)
   * @param {string} taskId - Identifiant de la tâche
   * @param {Object} options - Options de récupération
   * @returns {Promise<Object>} Résultat de la tâche
   */
  async getTaskResult(taskId, options = {}) {
    const maxWaitTime = options.timeout || 60000; // 1 minute par défaut
    const pollInterval = options.pollInterval || 1000; // 1 seconde par défaut
    const startTime = Date.now();

    // Fonction de vérification
    const checkTask = async () => {
      const task = await this.getTask(taskId);

      if (!task) {
        throw new Error(`Tâche "${taskId}" introuvable`);
      }

      if (task.status === "completed") {
        return task.result;
      }

      if (task.status === "failed") {
        throw new Error(task.error?.message || "Tâche échouée");
      }

      // Vérifier le timeout
      if (Date.now() - startTime > maxWaitTime) {
        throw new Error(`Timeout dépassé (${maxWaitTime}ms)`);
      }

      // Attendre avant de vérifier à nouveau
      await new Promise((resolve) => setTimeout(resolve, pollInterval));

      // Vérifier à nouveau
      return checkTask();
    };

    return checkTask();
  }

  /**
   * Annule une tâche en cours
   * @param {string} taskId - Identifiant de la tâche
   * @returns {Promise<boolean>} Succès de l'annulation
   */
  async cancelTask(taskId) {
    await this.ensureInitialized();

    const task = await this.getTask(taskId);

    if (!task) {
      throw new Error(`Tâche "${taskId}" introuvable`);
    }

    if (task.status === "completed" || task.status === "failed") {
      logger.warn(
        "AsyncTaskManager: Tentative d'annulation d'une tâche déjà terminée",
        {
          taskId,
          status: task.status,
        }
      );
      return false;
    }

    // Marquer la tâche comme annulée
    await this.updateTask(taskId, {
      status: "cancelled",
      error: {
        message: "Tâche annulée par l'utilisateur",
        code: "TASK_CANCELLED",
      },
    });

    logger.info("AsyncTaskManager: Tâche annulée", { taskId });

    return true;
  }

  /**
   * Nettoie les tâches anciennes
   * @returns {Promise<number>} Nombre de tâches supprimées
   */
  async cleanupTasks() {
    await this.ensureInitialized();

    const now = Date.now();
    const deletedCount = { memory: 0, redis: 0 };

    // Nettoyage en mémoire
    for (const [taskId, task] of this.tasks.entries()) {
      const taskAge = now - new Date(task.updatedAt).getTime();
      const isCompleted = ["completed", "failed", "cancelled"].includes(
        task.status
      );

      // Supprimer les tâches terminées depuis plus de 1 heure
      if (isCompleted && taskAge > 3600000) {
        this.tasks.delete(taskId);
        deletedCount.memory++;
      }

      // Supprimer les tâches qui ont dépassé leur timeout
      if (!isCompleted && task.timeout && taskAge > task.timeout) {
        await this.updateTask(taskId, {
          status: "failed",
          error: {
            message: "Tâche expirée (timeout)",
            code: "TASK_TIMEOUT",
          },
        });

        deletedCount.memory++;
      }
    }

    // Si Redis est disponible, on ne fait pas de nettoyage explicite
    // car on a défini un TTL à la création des tâches

    if (deletedCount.memory > 0) {
      logger.info("AsyncTaskManager: Nettoyage des tâches", {
        deletedCount,
      });
    }

    return deletedCount.memory + deletedCount.redis;
  }
}

// Singleton
const taskManager = new AsyncTaskManager();

module.exports = taskManager;
