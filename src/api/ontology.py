"""
Ontology API Router - Based on catalog metadata
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.ontology import (
    OntologyDomain, OntologyStats, OntologyVisualizationData
)
from src.services.ontology_service import ontology_service
from src.config.logging_config import get_service_logger

router = APIRouter(prefix="/ontology", tags=["Ontology"])
logger = get_service_logger("ontology_api")

class OntologyDomainResponse(BaseModel):
    """Ontology domain response model"""
    id: str
    name: str
    description: Optional[str] = None
    entity_count: int
    relationship_count: int
    data_source_id: Optional[str] = None
    database_name: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None

class OntologySyncResponse(BaseModel):
    """Ontology sync response model"""
    success: bool
    message: str
    stats: Dict[str, Any] = {}

@router.get("/stats", response_model=OntologyStats)
async def get_ontology_stats():
    """Get ontology statistics"""
    try:
        logger.info("Getting ontology statistics")
        
        stats = await ontology_service.get_ontology_stats()
        
        logger.success(f"Retrieved ontology stats: {stats.total_domains} domains, {stats.total_entities} entities")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get ontology stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology statistics: {str(e)}")

@router.get("/domains", response_model=List[OntologyDomainResponse])
async def get_ontology_domains():
    """Get all ontology domains"""
    try:
        logger.info("Getting all ontology domains")
        
        domains = await ontology_service.get_ontology_domains()
        
        # Convert to response format
        response = []
        for domain in domains:
            response.append(OntologyDomainResponse(
                id=domain.id,
                name=domain.name,
                description=domain.description,
                entity_count=len(domain.entities),
                relationship_count=len(domain.relationships),
                data_source_id=domain.data_source_id,
                database_name=domain.database_name,
                tags=domain.tags,
                created_at=domain.created_at,
                updated_at=domain.updated_at,
                last_sync_at=domain.last_sync_at
            ))
        
        logger.success(f"Retrieved {len(response)} ontology domains")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get ontology domains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology domains: {str(e)}")

@router.get("/domains/{domain_id}", response_model=OntologyDomain)
async def get_ontology_domain(domain_id: str):
    """Get specific ontology domain with full details"""
    try:
        logger.info(f"Getting ontology domain: {domain_id}")
        
        domain = await ontology_service.get_ontology_domain(domain_id)
        
        if not domain:
            raise HTTPException(status_code=404, detail="Ontology domain not found")
        
        logger.success(f"Retrieved ontology domain: {domain.name}")
        return domain
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ontology domain {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ontology domain: {str(e)}")

@router.get("/domains/{domain_id}/visualization", response_model=OntologyVisualizationData)
async def get_domain_visualization(domain_id: str):
    """Get visualization data for a specific domain"""
    try:
        logger.info(f"Getting visualization data for domain: {domain_id}")
        
        viz_data = await ontology_service.get_visualization_data(domain_id)
        
        if not viz_data:
            raise HTTPException(status_code=404, detail="Ontology domain not found or no visualization data available")
        
        logger.success(f"Retrieved visualization data: {len(viz_data.nodes)} nodes, {len(viz_data.edges)} edges")
        return viz_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get visualization data for {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {str(e)}")

@router.post("/sync", response_model=OntologySyncResponse)
async def sync_ontology_from_catalog(data_source_id: Optional[str] = Query(None, description="Specific data source to sync")):
    """Sync ontology from catalog metadata"""
    try:
        logger.info(f"Starting ontology sync from catalog, data_source_id: {data_source_id}")
        
        result = await ontology_service.sync_from_catalog(data_source_id)
        
        response = OntologySyncResponse(
            success=result["success"],
            message=result["message"],
            stats=result.get("stats", {})
        )
        
        if result["success"]:
            logger.success(f"Ontology sync completed: {result['stats']}")
        else:
            logger.warning(f"Ontology sync failed: {result['message']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Ontology sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ontology sync failed: {str(e)}")

@router.get("/domains/{domain_id}/entities")
async def get_domain_entities(domain_id: str):
    """Get entities for a specific domain"""
    try:
        logger.info(f"Getting entities for domain: {domain_id}")
        
        domain = await ontology_service.get_ontology_domain(domain_id)
        
        if not domain:
            raise HTTPException(status_code=404, detail="Ontology domain not found")
        
        logger.success(f"Retrieved {len(domain.entities)} entities for domain {domain_id}")
        return domain.entities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entities for domain {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain entities: {str(e)}")

@router.get("/domains/{domain_id}/relationships")
async def get_domain_relationships(domain_id: str):
    """Get relationships for a specific domain"""
    try:
        logger.info(f"Getting relationships for domain: {domain_id}")
        
        domain = await ontology_service.get_ontology_domain(domain_id)
        
        if not domain:
            raise HTTPException(status_code=404, detail="Ontology domain not found")
        
        logger.success(f"Retrieved {len(domain.relationships)} relationships for domain {domain_id}")
        return domain.relationships
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get relationships for domain {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain relationships: {str(e)}")

@router.get("/search")
async def search_ontology(
    q: str = Query(..., description="Search query"),
    domain_id: Optional[str] = Query(None, description="Domain to search in"),
    entity_type: Optional[str] = Query(None, description="Entity type filter")
):
    """Search ontology entities and relationships"""
    try:
        logger.info(f"Searching ontology: query='{q}', domain_id={domain_id}, entity_type={entity_type}")
        
        domains = await ontology_service.get_ontology_domains()
        
        # Filter by domain if specified
        if domain_id:
            domains = [d for d in domains if d.id == domain_id]
        
        results = []
        
        for domain in domains:
            # Search entities
            for entity in domain.entities:
                if (q.lower() in entity.name.lower() or 
                    (entity.description and q.lower() in entity.description.lower())):
                    
                    if not entity_type or entity.type.value == entity_type:
                        results.append({
                            "type": "entity",
                            "domain_id": domain.id,
                            "domain_name": domain.name,
                            "id": entity.id,
                            "name": entity.name,
                            "description": entity.description,
                            "entity_type": entity.type.value,
                            "source_table": entity.source_table,
                            "row_count": entity.row_count
                        })
            
            # Search relationships
            for relationship in domain.relationships:
                if (q.lower() in relationship.name.lower() or 
                    (relationship.description and q.lower() in relationship.description.lower())):
                    
                    results.append({
                        "type": "relationship",
                        "domain_id": domain.id,
                        "domain_name": domain.name,
                        "id": relationship.id,
                        "name": relationship.name,
                        "description": relationship.description,
                        "relationship_type": relationship.type.value,
                        "cardinality": relationship.cardinality
                    })
        
        logger.success(f"Found {len(results)} search results for query '{q}'")
        return {
            "query": q,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# === AI SUGGESTIONS API ENDPOINTS ===

class AddEntityRequest(BaseModel):
    """Request model for adding a new entity"""
    name: str = Field(..., description="Entity name")
    description: Optional[str] = Field(None, description="Entity description")
    properties: List[str] = Field(default_factory=list, description="Entity properties")
    entity_type: str = Field(default="table", description="Entity type")
    is_ai_suggested: bool = Field(default=False, description="Whether this entity was AI-suggested")

class AddRelationshipRequest(BaseModel):
    """Request model for adding a new relationship"""
    name: str = Field(..., description="Relationship name")
    description: Optional[str] = Field(None, description="Relationship description")
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    cardinality: str = Field(default="one-to-many", description="Relationship cardinality")
    is_ai_suggested: bool = Field(default=False, description="Whether this relationship was AI-suggested")

class EntityUpdateRequest(BaseModel):
    """Request model for updating an entity"""
    name: Optional[str] = Field(None, description="Entity name")
    description: Optional[str] = Field(None, description="Entity description")
    properties: Optional[List[str]] = Field(None, description="Entity properties")

@router.post("/domains/{domain_id}/entities")
async def add_entity_to_domain(domain_id: str, entity_request: AddEntityRequest):
    """Add a new entity to a domain"""
    try:
        logger.info(f"Adding entity '{entity_request.name}' to domain {domain_id}")
        
        result = await ontology_service.add_entity_to_domain(
            domain_id=domain_id,
            entity_name=entity_request.name,
            entity_description=entity_request.description,
            entity_properties=entity_request.properties,
            entity_type=entity_request.entity_type,
            is_ai_suggested=entity_request.is_ai_suggested
        )
        
        if result["success"]:
            logger.success(f"Entity '{entity_request.name}' added successfully to domain {domain_id}")
            return {
                "success": True,
                "message": f"Entity '{entity_request.name}' added successfully",
                "entity_id": result.get("entity_id"),
                "stats": result.get("stats", {})
            }
        else:
            logger.warning(f"Failed to add entity: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add entity to domain {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add entity: {str(e)}")

@router.put("/domains/{domain_id}/entities/{entity_id}")
async def update_entity(domain_id: str, entity_id: str, update_request: EntityUpdateRequest):
    """Update an existing entity"""
    try:
        logger.info(f"Updating entity {entity_id} in domain {domain_id}")
        
        result = await ontology_service.update_entity(
            domain_id=domain_id,
            entity_id=entity_id,
            updates=update_request.dict(exclude_none=True)
        )
        
        if result["success"]:
            logger.success(f"Entity {entity_id} updated successfully")
            return {
                "success": True,
                "message": "Entity updated successfully",
                "stats": result.get("stats", {})
            }
        else:
            logger.warning(f"Failed to update entity: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update entity {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update entity: {str(e)}")

@router.post("/domains/{domain_id}/relationships")
async def add_relationship_to_domain(domain_id: str, relationship_request: AddRelationshipRequest):
    """Add a new relationship to a domain"""
    try:
        logger.info(f"Adding relationship '{relationship_request.name}' to domain {domain_id}")
        
        result = await ontology_service.add_relationship_to_domain(
            domain_id=domain_id,
            relationship_name=relationship_request.name,
            relationship_description=relationship_request.description,
            source_entity_id=relationship_request.source_entity_id,
            target_entity_id=relationship_request.target_entity_id,
            cardinality=relationship_request.cardinality,
            is_ai_suggested=relationship_request.is_ai_suggested
        )
        
        if result["success"]:
            logger.success(f"Relationship '{relationship_request.name}' added successfully to domain {domain_id}")
            return {
                "success": True,
                "message": f"Relationship '{relationship_request.name}' added successfully",
                "relationship_id": result.get("relationship_id"),
                "stats": result.get("stats", {})
            }
        else:
            logger.warning(f"Failed to add relationship: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add relationship to domain {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add relationship: {str(e)}")

@router.delete("/domains/{domain_id}/entities/{entity_id}")
async def delete_entity(domain_id: str, entity_id: str):
    """Delete an entity from a domain"""
    try:
        logger.info(f"Deleting entity {entity_id} from domain {domain_id}")
        
        result = await ontology_service.delete_entity(domain_id, entity_id)
        
        if result["success"]:
            logger.success(f"Entity {entity_id} deleted successfully")
            return {
                "success": True,
                "message": "Entity deleted successfully",
                "stats": result.get("stats", {})
            }
        else:
            logger.warning(f"Failed to delete entity: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete entity: {str(e)}")

@router.delete("/domains/{domain_id}/relationships/{relationship_id}")
async def delete_relationship(domain_id: str, relationship_id: str):
    """Delete a relationship from a domain"""
    try:
        logger.info(f"Deleting relationship {relationship_id} from domain {domain_id}")
        
        result = await ontology_service.delete_relationship(domain_id, relationship_id)
        
        if result["success"]:
            logger.success(f"Relationship {relationship_id} deleted successfully")
            return {
                "success": True,
                "message": "Relationship deleted successfully",
                "stats": result.get("stats", {})
            }
        else:
            logger.warning(f"Failed to delete relationship: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete relationship {relationship_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}") 