import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import logging

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/python_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lucie-python-api")

# Création de l'application FastAPI
app = FastAPI(
    title="Lucie Python AI API",
    description="Backend Python pour les fonctionnalités d'IA de Lucie",
    version="0.1.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour la journalisation des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request: {request.method} {request.url.path} - Completed in {process_time:.4f}s")
    return response

# Modèles de données
class MessageRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

class MessageResponse(BaseModel):
    response: str
    timestamp: str
    messageId: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

# Route de base
@app.get("/")
async def root():
    return {
        "message": "API Lucie Python - Backend IA fonctionnel",
        "version": "0.1.0",
        "status": "operational"
    }

# Route de santé
@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

# Route pour le traitement des messages
@app.post("/process-message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    try:
        # Logger la réception du message
        logger.info(f"Traitement de message reçu - longueur: {len(request.message)}")
        
        # Pour l'instant, nous avons une simple réponse en écho
        # Dans une implémentation réelle, nous appellerions ici les modèles d'IA
        echo_response = f"Version Python: J'ai reçu votre message: {request.message}"
        
        # Simuler un délai de traitement (à supprimer en production)
        time.sleep(0.5)
        
        # Préparer et renvoyer la réponse
        message_id = f"msg_{int(time.time() * 1000)}"
        
        return MessageResponse(
            response=echo_response,
            timestamp=datetime.now().isoformat(),
            messageId=message_id,
            context={
                "processedBy": "python-basic-echo",
                "processingTime": "0.5s"
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de traitement: {str(e)}")

# Point d'entrée pour uvicorn
if __name__ == "__main__":
    # Créer le dossier logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Démarrer le serveur
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)