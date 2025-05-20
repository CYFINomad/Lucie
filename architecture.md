# Architecture hybride améliorée de Lucie (Python + Node.js/React)

> **Objectif du projet** : Créer un assistant IA personnel avancé (style Jarvis d'Iron Man) avec interface minimaliste, capable d'évolution continue, d'apprentissage autonome, d'intégration avec multiples IA du marché, et d'interconnexion des connaissances entre différents domaines.

## 🏗️ Structure du Projet

```
/lucie
│
├── /backend                    # Backend Node.js principal
│   ├── /core                   # Noyau de Lucie (orchestration)
│   │   ├── LucieCore.js        # Classe principale (orchestration)
│   │   ├── KnowledgeBase.js    # Interface avec la base de connaissances Python
│   │   ├── LearningEngine.js   # Interface avec le moteur d'apprentissage Python
│   │   └── VectorDatabase.js   # Interface avec la base vectorielle
│   │
│   ├── /domains                # Organisation par domaines métier (DDD)
│   │   ├── /conversation       # Domaine: Conversations
│   │   ├── /knowledge          # Domaine: Gestion des connaissances
│   │   ├── /learning           # Domaine: Apprentissage
│   │   ├── /agents             # Domaine: Agents
│   │   └── /system             # Domaine: Système
│   │
│   ├── /api                    # Gateway API principale
│   │   ├── /routes             # Routes API
│   │   ├── /middleware         # Middleware
│   │   ├── /controllers        # Contrôleurs génériques
│   │   └── /validation         # Validation des requêtes
│   │
│   ├── /python-bridge          # Communication avancée avec Python
│   │   ├── grpcClient.js       # Client gRPC pour communications hautes performances
│   │   ├── modelProxy.js       # Proxy pour les modèles IA
│   │   └── asyncTasks.js       # Gestionnaire de tâches asynchrones
│   │
│   ├── /utils                  # Utilitaires
│   │   ├── logger.js           # Journalisation avancée
│   │   ├── monitoring.js       # Surveillance des performances
│   │   ├── security.js         # Utilitaires de sécurité
│   │   └── config.js           # Configuration
│   │
│   ├── Dockerfile.node.dev     # Configuration Docker pour le développement
│   └── server.js               # Point d'entrée du serveur
│
├── /python-ai                  # Backend Python pour l'IA
│   ├── /domains                # Organisation par domaines métier (côté Python)
│   │   ├── /conversation       # Traitement des conversations
│   │   ├── /knowledge          # Gestion des connaissances
│   │   ├── /learning           # Apprentissage automatique
│   │   ├── /assistance         # Assistance proactive
│   │   └── /multi_ai           # Intégration d'IA externes
│   │
│   ├── /api                    # API FastAPI pour Python
│   │   ├── main.py             # Point d'entrée
│   │   ├── /routers            # Routeurs FastAPI
│   │   └── /schemas            # Schémas Pydantic
│   │
│   ├── /grpc                   # Service gRPC pour communication haute performance
│   │   ├── /protos             # Définitions protobuf
│   │   └── /services           # Implémentations des services
│   │
│   ├── /utils                  # Utilitaires Python
│   │   ├── logger.py           # Journalisation
│   │   └── config.py           # Configuration
│   │
│   ├── requirements.txt        # Dépendances Python
│   └── Dockerfile.python.dev   # Configuration Docker pour le développement
│
├── /lucie-ui                   # Interface utilisateur React
│   ├── /public                 # Fichiers statiques
│   ├── /src                    # Code source React
│   │   ├── /components         # Composants React
│   │   │   ├── /chat           # Composants de chat
│   │   │   ├── /knowledge      # Composants de connaissances
│   │   │   ├── /agents         # Composants d'agents
│   │   │   ├── /learning       # Composants d'apprentissage
│   │   │   ├── /assistant      # Composants spécifiques à l'assistant
│   │   │   ├── /ai-config      # Configuration des IA
│   │   │   └── /common         # Composants communs
│   │   │
│   │   ├── /pages              # Pages principales
│   │   ├── /services           # Services API
│   │   ├── /hooks              # Hooks personnalisés
│   │   ├── /utils              # Utilitaires frontend
│   │   ├── App.jsx             # Composant racine
│   │   └── index.jsx           # Point d'entrée
│   │
│   ├── package.json            # Dépendances frontend
│   ├── vite.config.js          # Configuration Vite
│   └── Dockerfile.ui.dev       # Configuration Docker pour le développement
│
├── /shared                     # Code partagé entre services
│   ├── /communication          # Communication inter-services
│   │   ├── /grpc               # Définitions gRPC partagées
│   │   └── /event-bus          # Bus d'événements
│   │
│   ├── /state                  # Gestion d'état distribuée
│   │   └── redis-client.js     # Client Redis
│   │
│   └── /schemas                # Schémas partagés
│       └── api-schemas.js      # Schémas API
│
├── /deployment                 # Configuration de déploiement
│   ├── /kubernetes             # Configurations Kubernetes
│   └── /docker                 # Configurations Docker
│
├── /scripts                    # Scripts utilitaires
│   └── dev.sh                  # Script de développement
│
├── docker-compose.dev.yml      # Configuration Docker Compose pour le développement
├── docker-compose.yml          # Configuration Docker Compose pour la production
├── package.json                # Dépendances racine et scripts
└── README.md                   # Documentation principale
```

## 🚀 Environnement de Développement

### Prérequis

- Docker et Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### Services de Développement

Le projet utilise Docker Compose pour orchestrer les services suivants en développement :

1. **Backend Node.js** (`lucie-node`)

   - Port: 5000 (API)
   - Port: 9229 (Debugger)
   - Hot-reload activé

2. **Backend Python** (`lucie-python`)

   - Port: 8000 (API FastAPI)
   - Port: 50051 (gRPC)
   - Port: 5678 (Debugger Python)
   - Hot-reload activé

3. **Frontend React** (`lucie-ui`)

   - Port: 3000
   - Hot-reload activé

4. **Bases de données**

   - Neo4j (Ports: 7474, 7687)
   - Redis (Port: 6379)
   - Weaviate (Port: 8080)

5. **Outils de développement**
   - Redis Commander (Port: 8081)

### Scripts de Développement

Le projet inclut un script `dev.sh` pour faciliter le développement :

```bash
./dev.sh start      # Démarre l'environnement
./dev.sh stop       # Arrête l'environnement
./dev.sh restart    # Redémarre l'environnement
./dev.sh logs       # Affiche les logs
./dev.sh clean      # Nettoie l'environnement
./dev.sh test       # Lance les tests
./dev.sh status     # Affiche l'état des services
```

## 🔄 Communication Inter-Services

1. **Node.js ↔ Python**

   - gRPC pour les communications hautes performances
   - REST API pour les opérations standard
   - Redis pour le cache et la synchronisation

2. **Frontend ↔ Backend**
   - REST API pour les opérations CRUD
   - WebSocket pour les mises à jour en temps réel
   - gRPC-Web pour les opérations hautes performances

## 🛠️ Outils de Développement

1. **Debugging**

   - Node.js: Debugger sur le port 9229
   - Python: Debugger sur le port 5678
   - React: React Developer Tools

2. **Monitoring**

   - Redis Commander pour Redis
   - Neo4j Browser pour Neo4j
   - Weaviate Console pour Weaviate

3. **Tests**
   - Jest pour Node.js
   - Pytest pour Python
   - React Testing Library pour le frontend

## 🔒 Sécurité

1. **Authentification**

   - JWT pour l'authentification API
   - Sessions sécurisées pour le frontend

2. **Autorisation**

   - RBAC (Role-Based Access Control)
   - Permissions granulaires

3. **Communication**
   - HTTPS pour toutes les communications
   - gRPC avec TLS
   - WebSocket sécurisé

## 📈 Scalabilité

1. **Architecture**

   - Services indépendants et scalables
   - Communication asynchrone
   - Cache distribué

2. **Performance**
   - Load balancing
   - Caching multi-niveaux
   - Optimisation des requêtes

## 🔄 CI/CD

1. **Intégration Continue**

   - Tests automatiques
   - Linting
   - Build automatique

2. **Déploiement Continu**
   - Déploiement automatique
   - Rollback automatique
   - Monitoring post-déploiement
