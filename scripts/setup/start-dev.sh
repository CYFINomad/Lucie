#!/bin/bash
# Script de démarrage du développement de Lucie

# Définir les couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Démarrage de l'environnement de développement Lucie ===${NC}"

# Vérifier si Docker est en cours d'exécution
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Docker n'est pas en cours d'exécution.${NC} Veuillez démarrer Docker et réessayer."
  exit 1
fi

# Créer un fichier .env s'il n'existe pas
if [ ! -f .env ]; then
  echo -e "${YELLOW}Fichier .env non trouvé.${NC} Création à partir de .env.example..."
  if [ -f .env.example ]; then
    cp .env.example .env
    echo -e "${GREEN}Fichier .env créé.${NC} Vérifiez les paramètres avant de continuer."
  else
    echo -e "${RED}Fichier .env.example non trouvé.${NC} Veuillez créer un fichier .env manuellement."
    exit 1
  fi
fi

# Vérifier les arguments
BUILD=false
LOGS=false
CLEAN=false

for arg in "$@"
do
  case $arg in
    --build)
      BUILD=true
      shift
      ;;
    --logs)
      LOGS=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    *)
      # Argument inconnu
      echo -e "${YELLOW}Argument inconnu:${NC} $arg"
      echo "Options disponibles: --build, --logs, --clean"
      shift
      ;;
  esac
done

# Clean si demandé
if [ "$CLEAN" = true ]; then
  echo -e "${YELLOW}Nettoyage des conteneurs et volumes...${NC}"
  docker-compose down -v
  echo -e "${GREEN}Nettoyage terminé.${NC}"
  
  # Si on nettoie seulement, on quitte
  if [ "$BUILD" = false ] && [ "$LOGS" = false ]; then
    exit 0
  fi
fi

# Arrêter les conteneurs existants
echo -e "${GREEN}Arrêt des conteneurs existants...${NC}"
docker-compose down

# Reconstruire si nécessaire
if [ "$BUILD" = true ]; then
  echo -e "${GREEN}Reconstruction des images...${NC}"
  docker-compose build
fi

# Démarrer les services
echo -e "${GREEN}Démarrage des services...${NC}"
docker-compose up -d

# Attendre que les services soient prêts
echo -e "${GREEN}Attente du démarrage des services...${NC}"
sleep 5

# Vérifier l'état des services
echo -e "${BLUE}État des services:${NC}"
docker-compose ps

echo -e "${BLUE}Lucie est prête pour le développement!${NC}"
echo -e "${GREEN}Interface utilisateur: ${NC}http://localhost:3000"
echo -e "${GREEN}API Backend: ${NC}http://localhost:5000"
echo -e "${GREEN}API Python: ${NC}http://localhost:8000"
echo -e "${GREEN}Interface Neo4j: ${NC}http://localhost:7474 (neo4j/password)"
echo -e "${GREEN}Redis Commander: ${NC}http://localhost:8081"

# Afficher les logs en temps réel si demandé
if [ "$LOGS" = true ]; then
  echo -e "${GREEN}Affichage des logs en temps réel...${NC}"
  docker-compose logs -f
fi