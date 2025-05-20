# Lucie - Assistant IA Personnel Avancé

> Lucie est un assistant IA personnel avancé inspiré du style Jarvis d'Iron Man, avec une interface minimaliste mais puissante, capable d'évolution continue, d'apprentissage autonome, d'intégration avec multiples IA, et d'interconnexion des connaissances entre différents domaines.

## 📋 Vue d'ensemble

Lucie est conçue comme une extension personnelle de votre cerveau, vous assistant dans diverses tâches tout en apprenant continuellement de vos interactions et préférences. L'architecture hybride utilise Python pour les capacités d'IA avancées et Node.js/React pour l'interface utilisateur.

### Fonctionnalités principales

- **Conversation naturelle** : Interface de chat intuitive pour interagir avec Lucie
- **Apprentissage continu** : Capacité à s'améliorer et à apprendre de nouvelles informations
- **Intégration multi-IA** : Orchestration de plusieurs modèles d'IA pour des tâches spécifiques
- **Interface minimaliste** : Design inspiré de Jarvis pour une expérience utilisateur élégante
- **Base de connaissances personnalisée** : Structure de données adaptée à vos besoins
- **Support vocal** : Reconnaissance et synthèse vocale pour une interaction naturelle
- **Avatar visuel** : Interface visuelle réactive et personnalisable
- **Proactivité** : Capacité à anticiper les besoins et à proposer des actions

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Node.js 18+ (pour le développement local)
- Python 3.11+ (pour le développement local)
- Git
- Au moins 8GB de RAM disponible
- 20GB d'espace disque libre

### Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-nom/lucie.git
   cd lucie
   ```

2. Démarrez l'environnement de développement :
   ```bash
   npm start
   ```

3. Accédez aux interfaces :
   - Interface utilisateur : http://localhost:3000
   - API Node.js : http://localhost:5000
   - API Python : http://localhost:8000
   - Neo4j Browser : http://localhost:7474
   - Redis Commander : http://localhost:8081

### Commandes utiles

```bash
# Démarrer l'environnement
npm start

# Arrêter l'environnement
npm run stop

# Redémarrer l'environnement
npm run restart

# Voir les logs
npm run logs

# Nettoyer l'environnement (supprime les volumes)
npm run clean

# Exécuter les tests
npm test

# Vérifier l'état des conteneurs
npm run status

# Linter le code
npm run lint

# Formater le code
npm run format
```

### Structure du projet

```
lucie/
├── backend/           # API Node.js
├── python-ai/         # Services Python et IA
├── lucie-ui/         # Interface utilisateur React
├── shared/           # Code partagé
├── shared-feedback/  # Données de feedback
└── deployment/       # Configurations de déploiement
```

### Développement

1. **Environnement de développement**
   - Hot-reload activé pour Node.js et Python
   - Debugging configuré pour VS Code
   - Linting et formatting automatiques

2. **Services disponibles**
   - Neo4j : Base de données graphe
   - Redis : Cache et message broker
   - Weaviate : Base de données vectorielle
   - Redis Commander : Interface d'administration Redis

3. **Bonnes pratiques**
   - Suivre les conventions de code définies dans `.eslintrc` et `.prettierrc`
   - Écrire des tests pour les nouvelles fonctionnalités
   - Documenter les changements majeurs
   - Utiliser les branches Git pour le développement

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
