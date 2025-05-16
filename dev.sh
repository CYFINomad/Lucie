#!/bin/bash
# Script pour gérer l'environnement de développement Docker

# Définir les couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher l'aide
show_help() {
  echo -e "${BLUE}Lucie - Script de développement Docker${NC}"
  echo -e "Utilisation: ./dev.sh [COMMANDE]"
  echo -e ""
  echo -e "Commandes disponibles:"
  echo -e "  ${GREEN}start${NC}      Démarre tous les conteneurs de développement"
  echo -e "  ${GREEN}stop${NC}       Arrête tous les conteneurs de développement"
  echo -e "  ${GREEN}restart${NC}    Redémarre tous les conteneurs de développement"
  echo -e "  ${GREEN}logs${NC}       Affiche les logs de tous les conteneurs"
  echo -e "  ${GREEN}node-logs${NC}  Affiche les logs du backend Node.js"
  echo -e "  ${GREEN}python-logs${NC} Affiche les logs du backend Python"
  echo -e "  ${GREEN}ui-logs${NC}    Affiche les logs du frontend React"
  echo -e "  ${GREEN}node-shell${NC} Ouvre un shell dans le conteneur Node.js"
  echo -e "  ${GREEN}python-shell${NC} Ouvre un shell dans le conteneur Python"
  echo -e "  ${GREEN}ui-shell${NC}   Ouvre un shell dans le conteneur React"
  echo -e "  ${GREEN}clean${NC}      Supprime tous les conteneurs et volumes"
  echo -e "  ${GREEN}test${NC}       Lance les tests"
  echo -e "  ${GREEN}status${NC}     Affiche l'état des conteneurs"
  echo -e "  ${GREEN}code${NC}       Ouvre VS Code avec la configuration de développement"
  echo -e "  ${GREEN}help${NC}       Affiche cette aide"
}

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
  echo -e "${RED}Docker ou Docker Compose n'est pas installé.${NC} Veuillez les installer avant de continuer."
  exit 1
fi

# Vérifier qu'un fichier docker-compose.dev.yml existe
if [ ! -f "docker-compose.dev.yml" ]; then
  echo -e "${RED}Le fichier docker-compose.dev.yml n'existe pas.${NC} Veuillez créer ce fichier avant de continuer."
  exit 1
fi

case "$1" in
  start)
    echo -e "${BLUE}Démarrage des conteneurs de développement...${NC}"
    docker-compose -f docker-compose.dev.yml up -d
    echo -e "${GREEN}Conteneurs démarrés!${NC}"
    echo -e "Interface utilisateur: ${BLUE}http://localhost:3000${NC}"
    echo -e "API Backend: ${BLUE}http://localhost:5000${NC}"
    echo -e "API Python: ${BLUE}http://localhost:8000${NC}"
    echo -e "Interface Neo4j: ${BLUE}http://localhost:7474${NC} (neo4j/password)"
    echo -e "Redis Commander: ${BLUE}http://localhost:8081${NC}"
    ;;
  
  stop)
    echo -e "${BLUE}Arrêt des conteneurs de développement...${NC}"
    docker-compose -f docker-compose.dev.yml stop
    echo -e "${GREEN}Conteneurs arrêtés.${NC}"
    ;;
  
  restart)
    echo -e "${BLUE}Redémarrage des conteneurs de développement...${NC}"
    docker-compose -f docker-compose.dev.yml restart
    echo -e "${GREEN}Conteneurs redémarrés!${NC}"
    ;;
  
  logs)
    echo -e "${BLUE}Affichage des logs de tous les conteneurs...${NC}"
    docker-compose -f docker-compose.dev.yml logs -f
    ;;
  
  node-logs)
    echo -e "${BLUE}Affichage des logs du backend Node.js...${NC}"
    docker-compose -f docker-compose.dev.yml logs -f lucie-node
    ;;
  
  python-logs)
    echo -e "${BLUE}Affichage des logs du backend Python...${NC}"
    docker-compose -f docker-compose.dev.yml logs -f lucie-python
    ;;
  
  ui-logs)
    echo -e "${BLUE}Affichage des logs du frontend React...${NC}"
    docker-compose -f docker-compose.dev.yml logs -f lucie-ui
    ;;
  
  node-shell)
    echo -e "${BLUE}Ouverture d'un shell dans le conteneur Node.js...${NC}"
    docker-compose -f docker-compose.dev.yml exec lucie-node /bin/bash || docker-compose -f docker-compose.dev.yml exec lucie-node /bin/sh
    ;;
  
  python-shell)
    echo -e "${BLUE}Ouverture d'un shell dans le conteneur Python...${NC}"
    docker-compose -f docker-compose.dev.yml exec lucie-python /bin/bash
    ;;
  
  ui-shell)
    echo -e "${BLUE}Ouverture d'un shell dans le conteneur React...${NC}"
    docker-compose -f docker-compose.dev.yml exec lucie-ui /bin/bash || docker-compose -f docker-compose.dev.yml exec lucie-ui /bin/sh
    ;;
  
  clean)
    echo -e "${YELLOW}Attention: Cette commande va supprimer tous les conteneurs et volumes associés à Lucie.${NC}"
    read -p "Êtes-vous sûr de vouloir continuer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${BLUE}Nettoyage des conteneurs et volumes...${NC}"
      docker-compose -f docker-compose.dev.yml down -v
      echo -e "${GREEN}Nettoyage terminé.${NC}"
    fi
    ;;
  
  test)
    echo -e "${BLUE}Lancement des tests...${NC}"
    echo -e "${YELLOW}Tests Node.js${NC}"
    docker-compose -f docker-compose.dev.yml exec lucie-node npm test
    
    echo -e "${YELLOW}Tests Python${NC}"
    docker-compose -f docker-compose.dev.yml exec lucie-python pytest
    
    echo -e "${GREEN}Tests terminés.${NC}"
    ;;
  
  status)
    echo -e "${BLUE}État des conteneurs:${NC}"
    docker-compose -f docker-compose.dev.yml ps
    ;;
  
  code)
    if command -v code &> /dev/null; then
      echo -e "${BLUE}Ouverture de VS Code...${NC}"
      code .
    else
      echo -e "${RED}VS Code n'est pas installé ou n'est pas dans le PATH.${NC}"
    fi
    ;;
  
  help)
    show_help
    ;;
  
  *)
    if [ -z "$1" ]; then
      show_help
    else
      echo -e "${RED}Commande inconnue:${NC} $1"
      echo -e "Utilisez './dev.sh help' pour voir les commandes disponibles."
    fi
    ;;
esac