"""
Application settings using Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application Settings
    app_name: str = "Ontology Platform"
    app_version: str = "1.0.0"
    app_env: str = "development"
    log_level: str = "INFO"
    
    # MinIO Settings
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_name: str = "ontology-data"
    
    # Unity Catalog Settings
    uc_endpoint: str = "http://localhost:8080/api/2.1/unity-catalog"
    uc_catalog_name: str = "ontology_catalog"
    
    # Ollama Settings
    ollama_endpoint: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
    # Trino Settings
    trino_host: str = "localhost"
    trino_port: int = 8080
    trino_user: str = "admin"
    trino_catalog: str = "memory"
    trino_schema: str = "default"
    trino_http_scheme: str = "http"
    trino_auth_username: Optional[str] = None
    trino_auth_password: Optional[str] = None
    
    # Search API Settings
    exa_api_key: Optional[str] = None
    duckduckgo_region: str = "us-en"
    
    # LLM API Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # AWS Settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Local LLM Settings
    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: Optional[str] = None
    
    # Database Settings
    database_url: str = "sqlite:///./ontology.db"
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 