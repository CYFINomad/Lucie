import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
from datetime import datetime

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import de l'application FastAPI
from api.main import app

# Client de test
client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()
    assert response.json()["version"] == "0.1.0"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()
    assert "version" in response.json()

def test_process_message():
    test_message = "Ceci est un message de test"
    response = client.post(
        "/process-message",
        json={"message": test_message, "context": {}}
    )
    
    assert response.status_code == 200
    assert "response" in response.json()
    assert "timestamp" in response.json()
    assert "messageId" in response.json()
    assert test_message in response.json()["response"]

def test_process_message_empty():
    response = client.post(
        "/process-message",
        json={"message": "", "context": {}}
    )
    
    # Le message ne doit pas être vide, mais l'API gère ce cas
    assert response.status_code == 200

def test_process_message_with_context():
    test_context = {"user": "test_user", "session": "abc123"}
    response = client.post(
        "/process-message",
        json={"message": "Test avec contexte", "context": test_context}
    )
    
    assert response.status_code == 200
    assert "context" in response.json()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])