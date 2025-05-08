/**
 * Classe principale du noyau de Lucie
 * Gère l'orchestration des différents composants
 */
class LucieCore {
    constructor() {
      this.components = new Map();
      this.initialized = false;
      this.services = {};
      console.log('Instance LucieCore créée');
    }
  
    /**
     * Initialise le noyau de Lucie et tous ses composants
     * @returns {Promise<boolean>} Succès de l'initialisation
     */
    async initialize() {
      try {
        console.log('Initialisation du noyau Lucie...');
        
        // Initialiser les composants de base
        // Dans une version plus complète, nous chargerions dynamiquement
        // les composants du noyau et leurs dépendances
  
        // Enregistrer les services de base
        this.services = {
          state: {
            conversationState: {}
          },
          version: '0.1.0',
          startTime: new Date()
        };
        
        this.initialized = true;
        console.log('Noyau Lucie initialisé avec succès');
        return true;
      } catch (error) {
        console.error('Erreur lors de l\'initialisation du noyau Lucie:', error);
        throw error;
      }
    }
  
    /**
     * Enregistre un composant dans le noyau
     * @param {string} name - Nom du composant
     * @param {Object} component - Instance du composant
     */
    registerComponent(name, component) {
      this.components.set(name, component);
      console.log(`Composant "${name}" enregistré`);
      return component;
    }
  
    /**
     * Récupère un composant enregistré
     * @param {string} name - Nom du composant
     * @returns {Object} Instance du composant
     */
    getComponent(name) {
      if (!this.components.has(name)) {
        throw new Error(`Composant "${name}" non trouvé`);
      }
      return this.components.get(name);
    }
    
    /**
     * Vérifie si un composant est enregistré
     * @param {string} name - Nom du composant
     * @returns {boolean} Vrai si le composant existe
     */
    hasComponent(name) {
      return this.components.has(name);
    }
    
    /**
     * Récupère l'état d'initialisation
     * @returns {Object} État actuel du noyau
     */
    getStatus() {
      return {
        initialized: this.initialized,
        componentsCount: this.components.size,
        uptime: new Date() - this.services.startTime,
        version: this.services.version
      };
    }
  }
  
  // Export d'une instance singleton
  const lucieCore = new LucieCore();
  
  module.exports = lucieCore;