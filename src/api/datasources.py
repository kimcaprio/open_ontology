"""
Data Sources API Router
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from src.models.schemas import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from src.services.data_source_service import data_source_service
from src.config.logging_config import get_service_logger

router = APIRouter(prefix="/datasources", tags=["Data Sources"])
logger = get_service_logger("datasources_api")

class ConnectionTestRequest(BaseModel):
    """Connection test request model"""
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    type: str = Field(default="database", description="Data source type")

class ConnectionTestResponse(BaseModel):
    """Connection test response model"""
    success: bool
    message: str
    server_info: Optional[Dict[str, Any]] = None

class MetadataScanResponse(BaseModel):
    """Metadata scan response model"""
    success: bool
    message: str
    metadata: Dict[str, Any] = None

@router.get("/", response_model=List[DataSourceResponse])
async def get_data_sources():
    """Get all data sources"""
    try:
        logger.info("Getting all data sources")
        
        data_sources = await data_source_service.get_data_sources()
        
        # Convert to response format
        response = []
        for ds in data_sources:
            response.append(DataSourceResponse(
                id=ds.id,
                name=ds.name,
                description=ds.description,
                type=ds.type,
                connection_config=ds.connection_config,
                tags=ds.tags,
                created_at=ds.created_at,
                updated_at=ds.updated_at,
                last_scan_at=ds.last_scan_at,
                status=ds.status
            ))
        
        logger.success(f"Retrieved {len(response)} data sources")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get data sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources: {str(e)}")

@router.post("/", response_model=DataSourceResponse)
async def create_data_source(data_source: DataSourceCreate):
    """Create a new data source"""
    try:
        logger.info(f"Creating data source: {data_source.name}")
        
        # Convert to dict
        data = {
            "name": data_source.name,
            "description": data_source.description,
            "type": data_source.type,
            "connection_config": data_source.connection_config,
            "tags": data_source.tags or []
        }
        
        created_ds = await data_source_service.create_data_source(data)
        
        response = DataSourceResponse(
            id=created_ds.id,
            name=created_ds.name,
            description=created_ds.description,
            type=created_ds.type,
            connection_config=created_ds.connection_config,
            tags=created_ds.tags,
            created_at=created_ds.created_at,
            updated_at=created_ds.updated_at,
            last_scan_at=created_ds.last_scan_at,
            status=created_ds.status
        )
        
        logger.success(f"Created data source: {created_ds.name} (ID: {created_ds.id})")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create data source: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create data source: {str(e)}")

@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(data_source_id: str):
    """Get a specific data source"""
    try:
        logger.info(f"Getting data source: {data_source_id}")
        
        data_source = await data_source_service.get_data_source(data_source_id)
        
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        response = DataSourceResponse(
            id=data_source.id,
            name=data_source.name,
            description=data_source.description,
            type=data_source.type,
            connection_config=data_source.connection_config,
            tags=data_source.tags,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at,
            last_scan_at=data_source.last_scan_at,
            status=data_source.status
        )
        
        logger.success(f"Retrieved data source: {data_source.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get data source {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get data source: {str(e)}")

@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source(data_source_id: str, update_data: DataSourceUpdate):
    """Update a data source"""
    try:
        logger.info(f"Updating data source: {data_source_id}")
        
        # Convert to dict, excluding None values
        data = {}
        if update_data.name is not None:
            data["name"] = update_data.name
        if update_data.description is not None:
            data["description"] = update_data.description
        if update_data.connection_config is not None:
            data["connection_config"] = update_data.connection_config
        if update_data.tags is not None:
            data["tags"] = update_data.tags
        
        updated_ds = await data_source_service.update_data_source(data_source_id, data)
        
        if not updated_ds:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        response = DataSourceResponse(
            id=updated_ds.id,
            name=updated_ds.name,
            description=updated_ds.description,
            type=updated_ds.type,
            connection_config=updated_ds.connection_config,
            tags=updated_ds.tags,
            created_at=updated_ds.created_at,
            updated_at=updated_ds.updated_at,
            last_scan_at=updated_ds.last_scan_at,
            status=updated_ds.status
        )
        
        logger.success(f"Updated data source: {updated_ds.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update data source {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update data source: {str(e)}")

@router.delete("/{data_source_id}")
async def delete_data_source(data_source_id: str):
    """Delete a data source"""
    try:
        logger.info(f"Deleting data source: {data_source_id}")
        
        success = await data_source_service.delete_data_source(data_source_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        logger.success(f"Deleted data source: {data_source_id}")
        return {"message": "Data source deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete data source {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete data source: {str(e)}")

@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest):
    """Test database connection"""
    try:
        logger.info(f"Testing connection for type: {request.type}")
        
        result = await data_source_service.test_connection(
            request.connection_config, 
            request.type
        )
        
        response = ConnectionTestResponse(
            success=result["success"],
            message=result["message"],
            server_info=result.get("server_info")
        )
        
        if result["success"]:
            logger.success("Connection test successful")
        else:
            logger.warning(f"Connection test failed: {result['message']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/{data_source_id}/scan", response_model=MetadataScanResponse)
async def scan_metadata(data_source_id: str):
    """Scan metadata from a data source"""
    try:
        logger.info(f"Scanning metadata for data source: {data_source_id}")
        
        result = await data_source_service.scan_metadata(data_source_id)
        
        response = MetadataScanResponse(
            success=result["success"],
            message=result["message"],
            metadata=result.get("metadata")
        )
        
        if result["success"]:
            logger.success(f"Metadata scan completed for {data_source_id}")
        else:
            logger.warning(f"Metadata scan failed for {data_source_id}: {result['message']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Metadata scan error for {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metadata scan failed: {str(e)}")

@router.get("/{data_source_id}/health")
async def check_data_source_health(data_source_id: str):
    """Check data source health status"""
    try:
        logger.info(f"Checking health for data source: {data_source_id}")
        
        data_source = await data_source_service.get_data_source(data_source_id)
        
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        # Test connection to check health
        result = await data_source_service.test_connection(
            data_source.connection_config, 
            data_source.type
        )
        
        status = "healthy" if result["success"] else "unhealthy"
        
        response = {
            "id": data_source_id,
            "name": data_source.name,
            "status": status,
            "last_check": str(datetime.utcnow()),
            "message": result["message"]
        }
        
        logger.info(f"Health check completed for {data_source_id}: {status}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed for {data_source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}") 