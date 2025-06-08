"""
LLM (Large Language Model) API Router
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config.logging_config import get_service_logger

router = APIRouter(prefix="/llm", tags=["LLM Models"])
logger = get_service_logger("llm_api")

class LLMModel(BaseModel):
    """LLM model information"""
    id: str
    name: str
    provider: str
    status: str
    description: Optional[str] = None
    capabilities: List[str] = []

class ModelsResponse(BaseModel):
    """Models list response"""
    models: List[LLMModel]
    total_count: int

@router.get("/models", response_model=ModelsResponse)
async def get_available_models():
    """Get list of available LLM models"""
    try:
        logger.info("Getting available LLM models")
        
        # For now, return demo models
        # In a real implementation, this would query actual LLM providers
        demo_models = [
            LLMModel(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                status="available",
                description="Fast and efficient model for general tasks",
                capabilities=["text-generation", "sql-generation", "code-completion"]
            ),
            LLMModel(
                id="gpt-4",
                name="GPT-4",
                provider="openai", 
                status="available",
                description="Most capable model for complex reasoning",
                capabilities=["text-generation", "sql-generation", "code-completion", "advanced-reasoning"]
            ),
            LLMModel(
                id="claude-3-sonnet",
                name="Claude 3 Sonnet",
                provider="anthropic",
                status="available",
                description="Balanced model for analysis and reasoning",
                capabilities=["text-generation", "sql-generation", "analysis"]
            ),
            LLMModel(
                id="claude-3-haiku",
                name="Claude 3 Haiku",
                provider="anthropic",
                status="available",
                description="Fast and lightweight model",
                capabilities=["text-generation", "sql-generation"]
            ),
            LLMModel(
                id="ollama-llama3.2",
                name="Llama 3.2 (Local)",
                provider="ollama",
                status="available",
                description="Local Llama model via Ollama",
                capabilities=["text-generation", "sql-generation"]
            ),
            LLMModel(
                id="ollama-qwen3",
                name="Qwen 3 (Local)",
                provider="ollama",
                status="available",
                description="Local Qwen model via Ollama",
                capabilities=["text-generation", "sql-generation"]
            ),
            LLMModel(
                id="gemini-pro",
                name="Gemini Pro",
                provider="google",
                status="unavailable",
                description="Google's advanced model (requires API key)",
                capabilities=["text-generation", "sql-generation", "multimodal"]
            ),
            LLMModel(
                id="bedrock-claude",
                name="Claude via Bedrock",
                provider="aws_bedrock",
                status="unavailable",
                description="Claude model via AWS Bedrock (requires AWS setup)",
                capabilities=["text-generation", "sql-generation"]
            )
        ]
        
        response = ModelsResponse(
            models=demo_models,
            total_count=len(demo_models)
        )
        
        logger.success(f"Retrieved {len(demo_models)} LLM models")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get LLM models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM models: {str(e)}")

@router.get("/models/{model_id}")
async def get_model_info(model_id: str):
    """Get detailed information about a specific model"""
    try:
        logger.info(f"Getting model info for: {model_id}")
        
        # Get models and find the requested one
        models_response = await get_available_models()
        model = next((m for m in models_response.models if m.id == model_id), None)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        logger.success(f"Retrieved model info for {model_id}")
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.get("/health")
async def llm_health_check():
    """Check LLM service health"""
    try:
        models_response = await get_available_models()
        available_models = [m for m in models_response.models if m.status == "available"]
        
        return {
            "status": "healthy",
            "total_models": models_response.total_count,
            "available_models": len(available_models),
            "providers": list(set(m.provider for m in models_response.models)),
            "timestamp": "2025-06-08T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM service unhealthy: {str(e)}") 