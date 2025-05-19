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

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Node.js 16+ (pour le développement local)
- Python 3.9+ (pour le développement local)
- Git

### Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-nom/lucie.git
   cd lucie
   docker-compose -f docker-compose.dev.yml up -d
   ```

View log : `docker logs containter-name`
Rebuild container: `docker-compose build`
Delete all container : `docker rm -f $(docker ps -aq)`
Delete all images : `docker system prune -a --volumes`
