"""
API principale pour le backend Python de Lucie
Gère les requêtes HTTP et coordonne les services
"""

import os
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/lucie_api.log", mode="a"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("lucie-python-api")

# Création de l'application FastAPI
app = FastAPI(
    title="Lucie Python AI API",
    description="Backend Python pour les capacités d'IA de Lucie",
    version="0.1.0",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modèles de données
class MessageRequest(BaseModel):
    """Modèle pour une requête de message"""

    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Modèle pour une réponse à un message"""

    response: str
    timestamp: str
    messageId: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ServiceMethod(BaseModel):
    """Modèle pour une méthode de service"""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Service(BaseModel):
    """Modèle pour un service"""

    name: str
    description: str
    status: str
    methods: List[ServiceMethod] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServicesResponse(BaseModel):
    """Modèle pour la réponse à une requête de liste des services"""

    services: List[Service]


class ServiceRequest(BaseModel):
    """Modèle pour une requête de service"""

    data: Dict[str, Any] = Field(default_factory=dict)


class ServiceResponse(BaseModel):
    """Modèle pour une réponse de service"""

    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ServiceStatus(BaseModel):
    """Modèle pour l'état d'un service"""

    status: str
    stats: Dict[str, Any] = Field(default_factory=dict)


# Middleware pour la journalisation des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour journaliser les requêtes HTTP"""
    start_time = time.time()

    # Tracer les détails de la requête
    logger.info(f"Request: {request.method} {request.url.path}")

    # Exécuter la requête
    response = await call_next(request)

    # Calculer le temps de traitement
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Completed in {process_time:.4f}s")

    return response


# Route de base
@app.get("/")
async def root():
    """Point d'entrée principal de l'API"""
    return {
        "message": "API Lucie Python - Backend IA fonctionnel",
        "version": "0.1.0",
        "status": "operational",
    }


# Route de santé
@app.get("/health")
async def health():
    """Vérifie l'état de santé de l'API"""
    # À terme, vérifier l'état des composants critiques
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "components": {
            "api": "ok",
            "conversation": _get_module_status("conversation"),
            "knowledge": _get_module_status("knowledge"),
            "learning": _get_module_status("learning"),
            "multi_ai": _get_module_status("multi_ai"),
        },
    }


def _get_module_status(module_name):
    """Vérifie l'état d'un module"""
    # Vérification simple pour le moment
    # À terme, interroger chaque module pour son état
    try:
        if module_name == "conversation" and conversation_module:
            return "ok"
        elif module_name == "knowledge" and knowledge_module:
            return "ok"
        elif module_name == "learning" and learning_module:
            return "ok"
        elif module_name == "multi_ai" and multi_ai_module:
            return "ok"
        else:
            return "not_loaded"
    except NameError:
        return "not_available"
    except Exception as e:
        logger.error(f"Error checking module {module_name}: {str(e)}")
        return "error"


# Route pour le traitement des messages
@app.post("/process-message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Traite un message de l'utilisateur et génère une réponse"""
    try:
        # Logger la réception du message
        logger.info(f"Message received - length: {len(request.message)}")

        # Pour l'instant, utilisation d'un traitement simplifié
        # À terme, utiliser le module de conversation

        # Essayer d'utiliser le module de conversation si disponible
        response_text = ""
        context = {}

        try:
            if "conversation_module" in globals() and conversation_module:
                # Utiliser le gestionnaire de dialogue
                dialog_manager = conversation_module.dialog_manager
                result = await dialog_manager.process_message(
                    request.message, request.context
                )
                response_text = result.get("response", "")
                context = result.get("context", {})
            else:
                # Réponse par défaut si le module n'est pas disponible
                response_text = f"J'ai bien reçu votre message: {request.message}\n\nLe module de conversation est en cours de développement et sera bientôt disponible."
        except Exception as e:
            logger.error(f"Error processing message with conversation module: {str(e)}")
            response_text = f"J'ai bien reçu votre message, mais une erreur s'est produite lors du traitement. L'équipe technique a été informée."

        # Générer un ID de message unique
        message_id = f"msg_{int(time.time() * 1000)}"

        # Préparer et renvoyer la réponse
        return MessageResponse(
            response=response_text,
            timestamp=datetime.now().isoformat(),
            messageId=message_id,
            context=context
            or {"processedBy": "python-basic-echo", "processingTime": "0.5s"},
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
        )


# Route pour lister les services disponibles
@app.get("/services", response_model=ServicesResponse)
async def list_services():
    """Liste les services disponibles"""
    services = []

    # Service de conversation
    if "conversation_module" in globals() and conversation_module:
        services.append(
            Service(
                name="conversation",
                description="Service de traitement de dialogue",
                status="available",
                methods=[
                    ServiceMethod(
                        name="process_message",
                        description="Traite un message et génère une réponse",
                        parameters={"message": "string", "context": "object"},
                    )
                ],
                metadata={"capabilities": ["dialog", "intent_recognition"]},
            )
        )
    else:
        services.append(
            Service(
                name="conversation",
                description="Service de traitement de dialogue",
                status="not_available",
                metadata={"error": "Module not loaded"},
            )
        )

    # Service de connaissances
    if "knowledge_module" in globals() and knowledge_module:
        services.append(
            Service(
                name="knowledge",
                description="Service de gestion des connaissances",
                status="available",
                methods=[
                    ServiceMethod(
                        name="query",
                        description="Recherche dans la base de connaissances",
                        parameters={"query": "string", "options": "object"},
                    ),
                    ServiceMethod(
                        name="addKnowledge",
                        description="Ajoute une connaissance",
                        parameters={"data": "object"},
                    ),
                    ServiceMethod(
                        name="getGraphStats",
                        description="Obtient des statistiques sur le graphe de connaissances",
                        parameters={},
                    ),
                ],
                metadata={"capabilities": ["semantic_search", "knowledge_graph"]},
            )
        )
    else:
        services.append(
            Service(
                name="knowledge",
                description="Service de gestion des connaissances",
                status="not_available",
                metadata={"error": "Module not loaded"},
            )
        )

    # Service d'apprentissage
    if "learning_module" in globals() and learning_module:
        services.append(
            Service(
                name="learning",
                description="Service d'apprentissage continu",
                status="available",
                methods=[
                    ServiceMethod(
                        name="processFeedback",
                        description="Traite le feedback utilisateur",
                        parameters={"feedback": "object"},
                    ),
                    ServiceMethod(
                        name="learnFromUrl",
                        description="Apprend à partir d'une URL",
                        parameters={"url": "string", "options": "object"},
                    ),
                    ServiceMethod(
                        name="identifyKnowledgeGaps",
                        description="Identifie les lacunes de connaissances",
                        parameters={"options": "object"},
                    ),
                    ServiceMethod(
                        name="getStats",
                        description="Obtient des statistiques sur l'apprentissage",
                        parameters={},
                    ),
                ],
                metadata={
                    "capabilities": [
                        "continuous_learning",
                        "url_extraction",
                        "feedback_processing",
                    ]
                },
            )
        )
    else:
        services.append(
            Service(
                name="learning",
                description="Service d'apprentissage continu",
                status="not_available",
                metadata={"error": "Module not loaded"},
            )
        )

    # Service Multi-AI
    if "multi_ai_module" in globals() and multi_ai_module:
        services.append(
            Service(
                name="multi_ai",
                description="Service d'orchestration d'IA multiples",
                status="available",
                methods=[
                    ServiceMethod(
                        name="listProviders",
                        description="Liste les fournisseurs d'IA disponibles",
                        parameters={},
                    ),
                    ServiceMethod(
                        name="generateResponse",
                        description="Génère une réponse via un modèle spécifique",
                        parameters={
                            "provider": "string",
                            "model": "string",
                            "prompt": "string",
                            "options": "object",
                        },
                    ),
                    ServiceMethod(
                        name="streamResponse",
                        description="Génère une réponse en streaming",
                        parameters={
                            "provider": "string",
                            "model": "string",
                            "prompt": "string",
                            "options": "object",
                        },
                    ),
                    ServiceMethod(
                        name="evaluateResponses",
                        description="Évalue plusieurs réponses",
                        parameters={
                            "query": "string",
                            "responses": "array",
                            "options": "object",
                        },
                    ),
                ],
                metadata={
                    "capabilities": ["multi_model", "response_evaluation", "streaming"]
                },
            )
        )
    else:
        services.append(
            Service(
                name="multi_ai",
                description="Service d'orchestration d'IA multiples",
                status="not_available",
                metadata={"error": "Module not loaded"},
            )
        )

    return ServicesResponse(services=services)


# Route pour vérifier l'état d'un service
@app.get("/services/{service_name}/status", response_model=ServiceStatus)
async def get_service_status(service_name: str):
    """Vérifie l'état d'un service spécifique"""
    # Vérifier si le service existe
    if service_name == "conversation":
        if "conversation_module" in globals() and conversation_module:
            return ServiceStatus(
                status="available",
                stats=(
                    conversation_module.get_stats()
                    if hasattr(conversation_module, "get_stats")
                    else {}
                ),
            )
    elif service_name == "knowledge":
        if "knowledge_module" in globals() and knowledge_module:
            return ServiceStatus(
                status="available",
                stats=(
                    knowledge_module.get_stats()
                    if hasattr(knowledge_module, "get_stats")
                    else {}
                ),
            )
    elif service_name == "learning":
        if "learning_module" in globals() and learning_module:
            return ServiceStatus(
                status="available",
                stats=(
                    learning_module.get_stats()
                    if hasattr(learning_module, "get_stats")
                    else {}
                ),
            )
    elif service_name == "multi_ai":
        if "multi_ai_module" in globals() and multi_ai_module:
            return ServiceStatus(
                status="available",
                stats=(
                    multi_ai_module.get_stats()
                    if hasattr(multi_ai_module, "get_stats")
                    else {}
                ),
            )

    # Service non trouvé
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Service {service_name} not found or not available",
    )


# Route pour appeler une méthode de service
@app.post("/services/{service_name}/{method_name}", response_model=ServiceResponse)
async def invoke_service_method(
    service_name: str, method_name: str, request: ServiceRequest
):
    """Appelle une méthode sur un service spécifique"""
    # Vérifier si le service existe
    service = None

    if (
        service_name == "conversation"
        and "conversation_module" in globals()
        and conversation_module
    ):
        service = conversation_module
    elif (
        service_name == "knowledge"
        and "knowledge_module" in globals()
        and knowledge_module
    ):
        service = knowledge_module
    elif (
        service_name == "learning"
        and "learning_module" in globals()
        and learning_module
    ):
        service = learning_module
    elif (
        service_name == "multi_ai"
        and "multi_ai_module" in globals()
        and multi_ai_module
    ):
        service = multi_ai_module

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_name} not found or not available",
        )

    # Vérifier si la méthode existe
    if not hasattr(service, method_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Method {method_name} not found in service {service_name}",
        )

    try:
        # Appeler la méthode
        method = getattr(service, method_name)
        result = (
            await method(**request.data)
            if hasattr(method, "__await__")
            else method(**request.data)
        )

        # Convertir le résultat en dict si nécessaire
        if not isinstance(result, dict):
            if hasattr(result, "__dict__"):
                result = result.__dict__
            else:
                result = {"value": result}

        return ServiceResponse(result=result)
    except Exception as e:
        logger.error(f"Error invoking {service_name}.{method_name}: {str(e)}")
        return ServiceResponse(result={}, error=str(e))


# Initialisation des modules
try:
    from domains.conversation import dialog_manager

    conversation_module = dialog_manager
    logger.info("Conversation module loaded")
except ImportError as e:
    logger.warning(f"Could not import conversation module: {str(e)}")
    conversation_module = None

try:
    from domains.knowledge import knowledge_graph

    knowledge_module = knowledge_graph
    logger.info("Knowledge module loaded")
except ImportError as e:
    logger.warning(f"Could not import knowledge module: {str(e)}")
    knowledge_module = None

try:
    from domains.learning import continuous_learning

    learning_module = continuous_learning
    logger.info("Learning module loaded")
except ImportError as e:
    logger.warning(f"Could not import learning module: {str(e)}")
    learning_module = None

try:
    from domains.multi_ai import ai_orchestrator

    multi_ai_module = ai_orchestrator
    logger.info("Multi-AI module loaded")
except ImportError as e:
    logger.warning(f"Could not import multi_ai module: {str(e)}")
    multi_ai_module = None

# Point d'entrée pour uvicorn
if __name__ == "__main__":
    # Créer le dossier logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)

    # Démarrer le serveur
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
