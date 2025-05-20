from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_DEBUG: bool = False

    # gRPC Settings
    GRPC_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50051

    # Database Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Weaviate Settings
    WEAVIATE_URL: str = "http://localhost:8080"

    # AI Model Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("logs")

    # Security Settings
    JWT_SECRET_KEY: str = Field(default="your-secret-key", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_database_url(self) -> str:
        """Get the database URL for Neo4j."""
        return f"bolt://{self.NEO4J_USER}:{self.NEO4J_PASSWORD}@{self.NEO4J_URI}"

    def get_redis_url(self) -> str:
        """Get the Redis URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_grpc_address(self) -> str:
        """Get the gRPC server address."""
        return f"{self.GRPC_HOST}:{self.GRPC_PORT}"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
