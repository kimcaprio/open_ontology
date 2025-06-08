"""
System status and health check API endpoints
"""

from fastapi import APIRouter, Depends
from loguru import logger

from src.config import get_settings, Settings
from src.models.schemas import SystemStatusResponse
from src.services.minio_service import MinioService
from src.services.ollama_service import OllamaService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "message": "API server is running"}


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(settings: Settings = Depends(get_settings)):
    """Get comprehensive system status"""
    logger.info("Checking system status")
    
    status = SystemStatusResponse()
    
    # Check MinIO connection
    try:
        minio_service = MinioService(settings)
        status.minio = await minio_service.health_check()
    except Exception as e:
        logger.warning(f"MinIO health check failed: {e}")
        status.minio = False
    
    # Check Unity Catalog connection
    try:
        # This will be implemented when Unity Catalog service is ready
        status.unity_catalog = False  # await check_unity_catalog_connection(settings)
    except Exception as e:
        logger.warning(f"Unity Catalog health check failed: {e}")
        status.unity_catalog = False
    
    # Check Ollama connection
    try:
        ollama_service = OllamaService(settings)
        status.ollama = await ollama_service.health_check()
        await ollama_service.close()
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        status.ollama = False
    
    # Database is always available for SQLite
    status.database = True
    
    logger.info(f"System status check completed: {status.model_dump()}")
    return status


@router.get("/version")
async def get_version(settings: Settings = Depends(get_settings)):
    """Get application version information"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env
    } 